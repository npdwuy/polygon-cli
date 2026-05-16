import fs from 'fs-extra';
import path from 'path';
import crypto from 'crypto';
import { z } from 'zod';

// --- Schemas ---

export const SolutionSchema = z.object({
  path: z.string(),
  tag: z.enum(['MA', 'TL', 'WA', 'OK', 'RJ', 'TO', 'TM', 'PE', 'ML', 'NR', 'RE']),
});

export const SubtaskSchema = z.object({
  id: z.number(),
  percent: z.number(),
  args: z.string().optional(), // Additional arguments for generator
});

export const ProblemSchema = z.object({
  local_id: z.string(),
  polygon_id: z.number().optional(),
  name: z.string(),
  paths: z.object({
    generator: z.string(),
    statement: z.string(),
    solutions: z.array(SolutionSchema),
  }),
  settings: z.object({
    time_limit: z.number().default(1000),
    memory_limit: z.number().default(1024),
    checker: z.string().default('std::lcmp.cpp'),
    compiler: z.string().default('cpp.gcc14-64-msys2-g++23'),
    auto_distribute_100_points: z.boolean().default(true),
  }),
  test_config: z.object({
    total_tests: z.number(),
    number_of_samples: z.number().default(1),
    subtasks: z.array(SubtaskSchema),
  }),
  pipeline_status: z.object({
    SETUP: z.boolean().default(false),
    MAIN: z.boolean().default(false),
    GEN: z.boolean().default(false),
    TESTS: z.boolean().default(false),
    BUILD: z.enum(['PENDING', 'RUNNING', 'READY', 'FAILED', 'NONE']).default('NONE'),
  }),
});

export type Problem = z.infer<typeof ProblemSchema>;

export const ProblemRegistrySchema = z.object({
  problems: z.array(ProblemSchema),
});

// --- Manager ---

export class WorkspaceManager {
  private rootDir: string;
  private problemJsonPath: string;
  private contestJsonPath: string;

  constructor(rootDir: string = process.cwd()) {
    this.rootDir = rootDir;
    this.problemJsonPath = path.join(this.rootDir, 'problem.json');
    this.contestJsonPath = path.join(this.rootDir, 'contest.json');
  }

  async ensureStructure() {
    await fs.ensureDir(path.join(this.rootDir, 'problems'));
    if (!await fs.pathExists(this.problemJsonPath)) {
      await fs.writeJson(this.problemJsonPath, { problems: [] }, { spaces: 2 });
    }
    if (!await fs.pathExists(this.contestJsonPath)) {
      await fs.writeJson(this.contestJsonPath, { contests: [] }, { spaces: 2 });
    }
  }

  async getProblems(): Promise<Problem[]> {
    const data = await fs.readJson(this.problemJsonPath);
    return ProblemRegistrySchema.parse(data).problems;
  }

  async saveProblems(problems: Problem[]) {
    await fs.writeJson(this.problemJsonPath, { problems }, { spaces: 2 });
  }

  async getProblemBySlug(slug: string): Promise<Problem | undefined> {
    const problems = await this.getProblems();
    return problems.find(p => p.local_id === slug);
  }

  async updateProblem(slug: string, updates: Partial<Problem>) {
    const problems = await this.getProblems();
    const index = problems.findIndex(p => p.local_id === slug);
    if (index !== -1) {
      problems[index] = { ...problems[index], ...updates } as Problem;
      await this.saveProblems(problems);
    }
  }

  async getFileHash(filePath: string): Promise<string> {
    if (!await fs.pathExists(filePath)) return '';
    const content = await fs.readFile(filePath);
    return crypto.createHash('sha256').update(content).digest('hex');
  }
}
