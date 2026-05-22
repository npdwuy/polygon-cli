import { PolygonAPI } from './polygon';
import { WorkspaceManager, Problem } from './workspace';
import fs from 'fs-extra';
import path from 'path';
import { execSync } from 'child_process';

export class SyncPipeline {
  constructor(
    private api: PolygonAPI,
    private workspace: WorkspaceManager
  ) {}

  async run(problemSlug: string) {
    const problem = await this.workspace.getProblemBySlug(problemSlug);
    if (!problem) {
      throw new Error(`Problem ${problemSlug} not found in registry.`);
    }

    console.log(`Starting sync pipeline for: ${problem.name} (${problemSlug})`);

    // 1. SETUP
    if (!problem.polygon_id) {
      console.log('Step SETUP: Creating problem on Polygon...');
      const createdProblem = await this.api.call<any>('problem.create', { name: problem.local_id });
      problem.polygon_id = createdProblem.id;
      await this.workspace.updateProblem(problemSlug, { polygon_id: problem.polygon_id });
    }

    const pId = { problemId: problem.polygon_id };

    console.log('Step SETUP: Updating basic info and checker...');
    await this.api.call('problem.updateInfo', {
      ...pId,
      timeLimit: problem.settings.time_limit,
      memoryLimit: problem.settings.memory_limit,
    });
    await this.api.call('problem.setChecker', { ...pId, checker: problem.settings.checker });

    if (await fs.pathExists(problem.paths.statement)) {
      console.log('Step SETUP: Saving statement...');
      const statementContent = await fs.readFile(problem.paths.statement, 'utf-8');
      await this.api.call('problem.saveStatement', {
        ...pId,
        lang: 'vietnamese', // Default lang, can be customized
        legend: statementContent,
      });
    }

    // 2. SOLUTIONS
    console.log('Step SOLUTIONS: Uploading solutions...');
    for (const sol of problem.paths.solutions) {
      if (await fs.pathExists(sol.path)) {
        const solContent = await fs.readFile(sol.path, 'utf-8');
        await this.api.call('problem.saveSolution', {
          ...pId,
          name: path.basename(sol.path),
          file: solContent,
          tag: sol.tag,
        });
      }
    }

    // 3. GEN
    if (await fs.pathExists(problem.paths.generator)) {
      console.log('Step GEN: Uploading generator...');
      const genContent = await fs.readFile(problem.paths.generator, 'utf-8');
      await this.api.call('problem.saveFile', {
        ...pId,
        type: 'source',
        name: path.basename(problem.paths.generator),
        file: genContent,
      });
    }

    // 4. TESTS (Dynamic Script Generation)
    console.log('Step TESTS: Generating and uploading script...');
    const scriptLines: string[] = [];
    let currentTest = 1;

    for (const subtask of problem.test_config.subtasks) {
      const numTests = Math.floor((subtask.percent / 100) * problem.test_config.total_tests);
      for (let i = 0; i < numTests; i++) {
        // Format: generator <seed> <subtask_id> <other_args>
        const args = subtask.args ? ` ${subtask.args}` : '';
        scriptLines.push(`${path.parse(problem.paths.generator).name} ${currentTest} ${subtask.id}${args} > ${currentTest}`);
        currentTest++;
      }
    }

    const scriptContent = scriptLines.join('\n');
    const scriptPath = path.join(path.dirname(problem.paths.generator), 'script.txt');
    console.log(`Step TESTS: Saving script locally to ${scriptPath}...`);
    await fs.writeFile(scriptPath, scriptContent, 'utf-8');

    await this.api.call('problem.saveScript', {
      ...pId,
      testset: 'tests', // Default testset
      source: scriptContent,
    });

    // 5. COMMIT
    console.log('Step COMMIT: Committing changes...');
    await this.api.call('problem.commitChanges', { ...pId, message: 'Auto-sync from DWUY Tool' });

    console.log('Sync pipeline completed successfully!');
  }

  async downloadPackage(problemSlug: string) {
    const problem = await this.workspace.getProblemBySlug(problemSlug);
    if (!problem || !problem.polygon_id) {
      throw new Error(`Problem ${problemSlug} not found or not synced.`);
    }

    const pId = { problemId: problem.polygon_id };

    console.log(`[${problemSlug}] Step BUILD: Triggering package build...`);
    try {
        await this.api.call('problem.buildPackage', { ...pId, verify: true, full: true });
    } catch (e: any) {
        if (e.message.includes('already being built') || e.message.includes('already non-failed full package')) {
            console.log(`[${problemSlug}] Package is already built or being built.`);
        } else {
            throw e;
        }
    }

    console.log(`[${problemSlug}] Step BUILD: Polling for package readiness...`);
    let packageId = -1;
    while (true) {
      const packages = await this.api.call<any[]>('problem.packages', pId);
      const latest = packages.sort((a, b) => b.id - a.id)[0];
      
      if (latest) {
        if (latest.state === 'READY') {
          packageId = latest.id;
          break;
        } else if (latest.state === 'FAILED') {
          throw new Error(`Package build failed: ${latest.comment}`);
        }
        console.log(`[${problemSlug}] Current state: ${latest.state}. Waiting...`);
      } else {
          console.log(`[${problemSlug}] No packages found. Waiting...`);
      }
      
      await new Promise(resolve => setTimeout(resolve, 5000));
    }

    console.log(`[${problemSlug}] Step DOWNLOAD: Downloading package ${packageId}...`);
    const buffer = await this.api.download('problem.package', { ...pId, packageId });
    
    const downloadDir = path.join(process.cwd(), 'downloads');
    await fs.ensureDir(downloadDir);
    const filePath = path.join(downloadDir, `${problemSlug}.zip`);
    await fs.writeFile(filePath, buffer);
    
    console.log(`[${problemSlug}] ✅ Package downloaded to: ${filePath}`);
    await this.workspace.updateProblem(problemSlug, { pipeline_status: { ...problem.pipeline_status, BUILD: 'READY' } });
  }

  async downloadPackagesParallel(slugs: string[]) {
    if (slugs.length === 0) {
      console.log('No slugs provided for parallel download.');
      return;
    }

    console.log(`Starting parallel build & download for ${slugs.length} problems: ${slugs.join(', ')}`);
    const results = await Promise.all(
      slugs.map(async (slug) => {
        try {
          await this.downloadPackage(slug);
          return { slug, success: true };
        } catch (error: any) {
          console.error(`[${slug}] ❌ Failed: ${error.message}`);
          return { slug, success: false, error: error.message };
        }
      })
    );

    const succeeded = results.filter(r => r.success).map(r => r.slug);
    const failed = results.filter(r => !r.success);

    console.log(`\n=== Download Summary ===`);
    console.log(`Succeeded (${succeeded.length}): ${succeeded.join(', ')}`);
    if (failed.length > 0) {
      console.log(`Failed (${failed.length}):`);
      failed.forEach(f => console.log(` - ${f.slug}: ${f.error}`));
    }
    console.log(`========================\n`);

    if (failed.length > 0) {
      throw new Error(`Failed to download packages for: ${failed.map(f => f.slug).join(', ')}`);
    }
  }

  async extractTests(problemSlug: string) {
    const problem = await this.workspace.getProblemBySlug(problemSlug);
    if (!problem) throw new Error(`Problem ${problemSlug} not found.`);

    const zipPath = path.join(process.cwd(), 'downloads', `${problemSlug}.zip`);
    if (!await fs.pathExists(zipPath)) {
      throw new Error(`ZIP file for ${problemSlug} not found in downloads/`);
    }

    const tempDir = path.join(process.cwd(), `temp_extract_${problemSlug}`);
    const destTestsDir = path.join(process.cwd(), 'problems', problemSlug, 'tests');

    console.log(`Step EXTRACT: Unzipping ${problemSlug}.zip...`);
    await fs.ensureDir(tempDir);
    execSync(`powershell -Command "Expand-Archive -Path '${zipPath}' -DestinationPath '${tempDir}' -Force"`);

    console.log(`Step BUILD: Running doall.bat...`);
    try {
      execSync(`cmd /c "cd /d ${tempDir} && doall.bat"`, { stdio: 'inherit' });
    } catch (e) {
      console.warn('Warning: doall.bat execution had errors, but continuing to check for tests...');
    }

    const generatedTestsDir = path.join(tempDir, 'tests');
    if (await fs.pathExists(generatedTestsDir)) {
      console.log(`Step MOVE: Moving generated tests to ${destTestsDir}...`);
      await fs.ensureDir(path.dirname(destTestsDir));
      if (await fs.pathExists(destTestsDir)) {
          await fs.remove(destTestsDir);
      }
      await fs.move(generatedTestsDir, destTestsDir);
      console.log(`✅ Tests successfully moved to ${destTestsDir}`);
    } else {
      throw new Error(`Failed to find generated 'tests' folder in ${tempDir}`);
    }

    console.log(`Step CLEANUP: Removing temporary directory ${tempDir}...`);
    await fs.remove(tempDir);
  }
}
