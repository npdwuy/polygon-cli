import fs from 'fs-extra';
import path from 'path';
import { execSync } from 'child_process';
import { WorkspaceManager } from './workspace';

export class ContestManager {
  constructor(private workspace: WorkspaceManager) {}

  async createContest(slugs: string[], contestName: string) {
    const rootDir = process.cwd();
    const contestsDir = path.join(rootDir, 'contests');
    const tempDir = path.join(rootDir, `temp_contest_${contestName}`);

    try {
      console.log(`🚀 Creating contest: ${contestName}`);
      
      // 1. Validate slugs
      for (const slug of slugs) {
        const problem = await this.workspace.getProblemBySlug(slug);
        if (!problem) {
          throw new Error(`Problem with slug "${slug}" not found.`);
        }
      }

      // 2. Prepare temp directory
      await fs.ensureDir(tempDir);
      await fs.ensureDir(contestsDir);

      // 3. Copy files for each problem
      for (const slug of slugs) {
        const problemDir = path.join(rootDir, 'problems', slug);
        const problemTestsDir = path.join(problemDir, 'tests');
        const problemMainFile = path.join(problemDir, 'main.cpp');

        // Create problem folder in contest
        const destProblemDir = path.join(tempDir, slug);
        await fs.ensureDir(destProblemDir);

        // Copy tests to the problem folder
        if (await fs.pathExists(problemTestsDir)) {
          console.log(`  - Copying tests for ${slug}...`);
          await fs.copy(problemTestsDir, destProblemDir);
        } else {
          console.warn(`  ⚠️ Warning: No tests found for ${slug}`);
        }

        // Copy main.cpp renamed to slug.cpp
        const destMainFile = path.join(tempDir, `${slug}.cpp`);
        if (await fs.pathExists(problemMainFile)) {
          console.log(`  - Copying main solution for ${slug}...`);
          await fs.copy(problemMainFile, destMainFile);
        } else {
          console.warn(`  ⚠️ Warning: No main solution found for ${slug}`);
        }
      }

      // 4. Zip the contest folder
      const zipPath = path.join(contestsDir, `${contestName}.zip`);
      console.log(`📦 Zipping contest into ${zipPath}...`);
      
      // Use powershell to compress. We zip the contents of tempDir so they are at the root of the zip.
      // We use '*' to include all files/folders inside tempDir.
      execSync(`powershell -Command "Compress-Archive -Path '${tempDir}\\*' -DestinationPath '${zipPath}' -Force"`);

      console.log(`✅ Contest "${contestName}" created successfully at ${zipPath}`);

    } catch (error: any) {
      console.error(`❌ Failed to create contest: ${error.message}`);
      throw error;
    } finally {
      // 5. Cleanup
      if (await fs.pathExists(tempDir)) {
        console.log(`🧹 Cleaning up temporary folder...`);
        await fs.remove(tempDir);
      }
    }
  }
}
