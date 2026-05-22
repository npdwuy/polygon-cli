import { Command } from 'commander';
import { PolygonAPI } from '../core/polygon';
import { WorkspaceManager } from '../core/workspace';
import { SyncPipeline } from '../core/pipeline';
import { ContestManager } from '../core/contest';
import path from 'path';
import fs from 'fs-extra';

const program = new Command();
const workspace = new WorkspaceManager();

program
  .name('polygon')
  .description('Polygon Management Tool - Developed by DWUY')
  .version('1.0.0');

program
  .command('config')
  .description('Set Polygon API credentials')
  .argument('<key>', 'Polygon API Key')
  .argument('<secret>', 'Polygon API Secret')
  .action(async (key, secret) => {
    try {
      const envPath = path.join(process.cwd(), '.env');
      const content = `POLYGON_API_KEY=${key}\nPOLYGON_API_SECRET=${secret}\n`;
      await fs.writeFile(envPath, content);
      console.log('✅ API credentials saved to .env');
    } catch (error: any) {
      console.error('❌ Failed to save credentials:', error.message);
    }
  });

program
  .command('init')
  .description('Initialize the workspace')
  .action(async () => {
    try {
      await workspace.ensureStructure();
      console.log('✅ Workspace initialized successfully.');
    } catch (error: any) {
      console.error('❌ Failed to initialize workspace:', error.message);
    }
  });

program
  .command('add')
  .description('Add a new problem')
  .argument('<slug>', 'Problem slug (e.g., bai-1)')
  .requiredOption('-n, --name <name>', 'Display name of the problem')
  .action(async (slug, options) => {
    try {
      await workspace.ensureStructure();
      const problems = await workspace.getProblems();
      
      if (problems.find(p => p.local_id === slug)) {
        console.error(`❌ Problem with slug "${slug}" already exists.`);
        return;
      }

      const problemDir = path.join(process.cwd(), 'problems', slug);
      await fs.ensureDir(problemDir);

      const newProblem = {
        local_id: slug,
        name: options.name,
        paths: {
          generator: `problems/${slug}/generator.cpp`,
          statement: `problems/${slug}/statement.tex`,
          solutions: [{ path: `problems/${slug}/main.cpp`, tag: 'MA' as const }],
        },
        settings: {
          time_limit: 1000,
          memory_limit: 1024,
          checker: 'std::lcmp.cpp',
          compiler: 'cpp.gcc14-64-msys2-g++23',
          auto_distribute_100_points: true,
        },
        test_config: {
          total_tests: 10,
          number_of_samples: 1,
          subtasks: [{ id: 1, percent: 100 }],
        },
        pipeline_status: {
          BUILD: 'NONE' as const,
        },
      };

      // Create templates
      await fs.writeFile(path.join(problemDir, 'main.cpp'), '// Standard solution\n#include <iostream>\nusing namespace std;\nint main() {\n    return 0;\n}\n');
      await fs.writeFile(path.join(problemDir, 'generator.cpp'), '// Test generator\n#include "testlib.h"\n#include <iostream>\nusing namespace std;\nint main(int argc, char* argv[]) {\n    registerGen(argc, argv, 1);\n    return 0;\n}\n');
      await fs.writeFile(path.join(problemDir, 'statement.tex'), 'Đề bài ở đây...');

      problems.push(newProblem);
      await workspace.saveProblems(problems);

      console.log(`✅ Problem "${options.name}" added successfully.`);
      console.log(`📁 Files created in problems/${slug}/`);
    } catch (error: any) {
      console.error('❌ Failed to add problem:', error.message);
    }
  });



program
  .command('sync')
  .description('Sync a problem with Polygon')
  .argument('<slug>', 'Problem slug to sync')
  .action(async (slug) => {
    try {
      const api = new PolygonAPI();
      const pipeline = new SyncPipeline(api, workspace);
      await pipeline.run(slug);
      console.log(`✅ Sync completed for ${slug}`);
    } catch (error: any) {
      console.error(`❌ Sync failed for ${slug}:`, error.message);
    }
  });

program
  .command('download')
  .description('Build and download the problem package')
  .argument('<slug>', 'Problem slug to download')
  .action(async (slug) => {
    try {
      const api = new PolygonAPI();
      const pipeline = new SyncPipeline(api, workspace);
      await pipeline.downloadPackage(slug);
    } catch (error: any) {
      console.error(`❌ Download failed for ${slug}:`, error.message);
    }
  });

program
  .command('extract')
  .description('Download and extract tests from Polygon package')
  .argument('<slug>', 'Problem slug to extract')
  .action(async (slug) => {
    try {
      const api = new PolygonAPI();
      const pipeline = new SyncPipeline(api, workspace);
      await pipeline.downloadPackage(slug);
      await pipeline.extractTests(slug);
      console.log(`✅ All steps completed for ${slug}`);
    } catch (error: any) {
      console.error(`❌ Extraction failed for ${slug}:`, error.message);
    }
  });

program
  .command('status')
  .description('Show status of all problems')
  .action(async () => {
    try {
      const problems = await workspace.getProblems();
      if (problems.length === 0) {
        console.log('No problems registered.');
        return;
      }

      console.table(problems.map(p => ({
        ID: p.local_id,
        Name: p.name,
        PolygonID: p.polygon_id || 'N/A',
        BUILD: p.pipeline_status.BUILD,
      })));
    } catch (error: any) {
      console.error('❌ Failed to fetch status:', error.message);
    }
  });

program
  .command('contest')
  .description('Create a contest package from selected problems')
  .argument('<name>', 'Contest name (e.g., round-1)')
  .argument('<slugs...>', 'Problem slugs to include in the contest')
  .action(async (name, slugs) => {
    try {
      await workspace.ensureStructure();
      const manager = new ContestManager(workspace);
      await manager.createContest(slugs, name);
    } catch (error: any) {
      console.error('❌ Contest creation failed:', error.message);
    }
  });

try {
  program.parse();
} catch (error: any) {
  console.error('CRITICAL ERROR:', error);
  process.exit(1);
}
