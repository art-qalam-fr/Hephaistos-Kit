#!/usr/bin/env node

const { Command } = require('commander');
const fs = require('fs-extra');
const path = require('path');
const os = require('os');
const chalk = require('chalk');
const ora = require('ora');

const program = new Command();

// Get the package root directory (parent of bin/)
const packageRoot = path.dirname(__dirname);
const agentDir = path.join(packageRoot, '.agent');
const vscodeDir = path.join(packageRoot, '.vscode');

async function copyDirectory(src, dest, options = {}) {
  const spinner = ora(`Copying ${path.basename(src)}...`).start();
  
  try {
    if (await fs.pathExists(dest) && !options.force) {
      spinner.warn(`Directory ${dest} already exists. Use --force to overwrite.`);
      return false;
    }
    
    // Remove existing directory if force is true
    if (await fs.pathExists(dest) && options.force) {
      try {
        await fs.remove(dest);
      } catch (e) {
        // EBUSY : un process (watcher IDE, MCP, indexeur) tient le dossier.
        // Fallback : merge-copy par-dessus au lieu d'échouer toute l'installation.
        if (e.code === 'EBUSY' || e.code === 'EPERM') {
          spinner.warn(`${path.basename(dest)} verrouillé (${e.code}) — copie par fusion`);
        } else {
          throw e;
        }
      }
    }
    
    // Copy the entire directory with all contents
    await fs.copy(src, dest, {
      filter: (src) => {
        // Exclude only specific files we don't want
        const relativePath = path.relative(packageRoot, src);

        // Include everything except node_modules and some cache files
        if (relativePath.includes('node_modules')) return false;
        if (relativePath.includes('.git')) return false;
        if (relativePath.includes('logs')) return false;
        if (relativePath.includes('semantic-cache-data')) return false;
        if (relativePath.includes('__pycache__')) return false;
        // Fichiers runtime volatils : logs épars + pid (souvent verrouillés en écriture)
        if (/\.(log|pid)$/i.test(relativePath)) return false;

        return true;
      }
    });
    
    spinner.succeed(`Copied ${path.basename(src)} successfully`);
    return true;
  } catch (error) {
    spinner.fail(`Failed to copy ${path.basename(src)}: ${error.message}`);
    return false;
  }
}

async function initCommand(options) {
  console.log(chalk.blue.bold('🔥 Hephaistos-Kit Initialization'));
  console.log('');
  
  const targetDir = options.path || process.cwd();
  
  if (options.dryRun) {
    console.log(chalk.yellow('🔍 DRY RUN MODE - No files will be copied'));
    console.log('');
    console.log(`Source directories:`);
    console.log(`  .agent: ${agentDir}`);
    console.log(`  .vscode: ${vscodeDir}`);
    console.log(`Target directory: ${targetDir}`);
    return;
  }
  
  if (!options.quiet) {
    console.log(`Target directory: ${targetDir}`);
    console.log('');
  }
  
  let success = true;

  // En mode update/force : préserver les données locales de .agent/memory-database/
  // (les index vectoriels et caches du projet ne doivent jamais être écrasés)
  // + rules/local_rules.md (règles spécifiques au projet, absentes du template)
  const agentTargetDir = path.join(targetDir, '.agent');
  const memDbPath = path.join(agentTargetDir, 'memory-database');
  const memDbBackup = path.join(targetDir, `.agent-memory-database.preserve-${Date.now()}`);
  const localRulesPath = path.join(agentTargetDir, 'rules', 'local_rules.md');
  const localRulesBackup = path.join(targetDir, `.agent-local_rules.preserve-${Date.now()}`);
  let preservedMemDb = false;
  let preservedLocalRules = false;

  if (options.force && await fs.pathExists(memDbPath)) {
    try {
      await fs.move(memDbPath, memDbBackup);
      preservedMemDb = true;
      console.log(chalk.cyan('  ~ .agent/memory-database préservé (données locales)'));
    } catch (e) {
      console.log(chalk.yellow(`  ⚠ Impossible de préserver memory-database: ${e.message}`));
    }
  }

  if (options.force && await fs.pathExists(localRulesPath)) {
    try {
      await fs.copy(localRulesPath, localRulesBackup);
      preservedLocalRules = true;
      console.log(chalk.cyan('  ~ .agent/rules/local_rules.md préservé (règles du projet)'));
    } catch (e) {
      console.log(chalk.yellow(`  ⚠ Impossible de préserver local_rules.md: ${e.message}`));
    }
  }

  // Copy .agent directory
  if (await fs.pathExists(agentDir)) {
    const agentSuccess = await copyDirectory(agentDir, agentTargetDir, options);
    success = success && agentSuccess;
  } else {
    console.log(chalk.red('❌ .agent directory not found in package'));
    success = false;
  }
  
  // Restaurer .agent/memory-database préservé (le template n'en contient qu'un squelette)
  if (preservedMemDb) {
    try {
      const newMemDb = path.join(agentTargetDir, 'memory-database');
      if (await fs.pathExists(newMemDb)) {
        await fs.remove(newMemDb);
      }
      await fs.move(memDbBackup, memDbPath);
      console.log(chalk.green('  ✔ .agent/memory-database restauré'));
    } catch (e) {
      console.log(chalk.yellow(`  ⚠ Restauration memory-database échouée: ${e.message} (backup: ${memDbBackup})`));
    }
  }

  if (preservedLocalRules) {
    try {
      await fs.copy(localRulesBackup, localRulesPath, { overwrite: true });
      await fs.remove(localRulesBackup);
      console.log(chalk.green('  ✔ .agent/rules/local_rules.md restauré'));
    } catch (e) {
      console.log(chalk.yellow(`  ⚠ Restauration local_rules.md échouée: ${e.message} (backup: ${localRulesBackup})`));
    }
  }

  // Copy .vscode directory
  if (await fs.pathExists(vscodeDir)) {
    const vscodeTarget = path.join(targetDir, '.vscode');
    const vscodeSuccess = await copyDirectory(vscodeDir, vscodeTarget, options);
    success = success && vscodeSuccess;
  } else {
    console.log(chalk.yellow('⚠️  .vscode directory not found in package'));
  }
  
  // Create memory-database structure at project root (for local mode)
  const memoryDbDir = path.join(targetDir, 'memory-database');
  const memoryDbSubdirs = ['cache', 'graph', 'vector/qdrant', 'vector/zvec'];
  
  try {
    for (const subdir of memoryDbSubdirs) {
      const dirPath = path.join(memoryDbDir, subdir);
      if (!await fs.pathExists(dirPath)) {
        await fs.ensureDir(dirPath);
      }
    }
    console.log(chalk.green('✅ Created memory-database structure at project root'));
  } catch (error) {
    console.log(chalk.yellow(`⚠️  Could not create memory-database: ${error.message}`));
  }
  
  // Copy .env.example if it exists and .env doesn't
  const envExampleSource = path.join(packageRoot, '.env.example');
  const envTarget = path.join(targetDir, '.env');
  
  if (await fs.pathExists(envExampleSource) && !await fs.pathExists(envTarget)) {
    try {
      await fs.copy(envExampleSource, envTarget);
      console.log(chalk.green('✅ Created .env from .env.example (customize for your environment)'));
    } catch (error) {
      console.log(chalk.yellow(`⚠️  Could not copy .env.example: ${error.message}`));
    }
  }
  
  // Copy package.json if requested
  if (options.includePackage) {
    const packageSource = path.join(packageRoot, 'package.json');
    const packageTarget = path.join(targetDir, 'package.json');
    
    try {
      await fs.copy(packageSource, packageTarget);
      console.log(chalk.green('✅ Copied package.json successfully'));
    } catch (error) {
      console.log(chalk.red(`❌ Failed to copy package.json: ${error.message}`));
      success = false;
    }
  }
  
  console.log('');
  if (success) {
    console.log(chalk.green.bold('🚀 Hephaistos-Kit initialized successfully!'));
    if (!options.quiet) {
      console.log('');
      console.log(chalk.gray('Next steps:'));
      console.log(chalk.gray('  • Restart your IDE to load the new agents'));
      console.log(chalk.gray('  • Check .agent/ directory for all available skills'));
      console.log(chalk.gray('  • Use /help to see available workflows'));
    }
  } else {
    console.log(chalk.red.bold('❌ Initialization failed with errors'));
    process.exit(1);
  }
}

async function updateCommand(options) {
  console.log(chalk.blue.bold('🔄 Hephaistos-Kit Update'));
  
  // For now, update just calls init with force
  await initCommand({ ...options, force: true });
}

async function statusCommand(options) {
  console.log(chalk.blue.bold('📊 Hephaistos-Kit Status'));
  console.log('');
  
  const currentDir = process.cwd();
  const agentExists = await fs.pathExists(path.join(currentDir, '.agent'));
  const vscodeExists = await fs.pathExists(path.join(currentDir, '.vscode'));
  
  console.log(`Current directory: ${currentDir}`);
  console.log('');
  console.log('Installation status:');
  console.log(`  .agent directory: ${agentExists ? chalk.green('✅ Installed') : chalk.red('❌ Missing')}`);
  console.log(`  .vscode directory: ${vscodeExists ? chalk.green('✅ Installed') : chalk.red('❌ Missing')}`);
  
  if (agentExists) {
    const agentPath = path.join(currentDir, '.agent');
    const stats = await fs.stat(agentPath);
    console.log(`  .agent size: ${chalk.cyan(formatBytes(stats.size))}`);
    console.log(`  .agent modified: ${chalk.cyan(stats.mtime.toLocaleDateString())}`);
  }
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Program configuration
program
  .name('hephaistos-kit')
  .description('AI Agent templates with Skills, Agents, and Workflows')
  .version('2.0.0');

// Init command
program
  .command('init')
  .description('Install .agent and .vscode folders into your project')
  .option('-f, --force', 'Overwrite existing .agent folder')
  .option('-p, --path <path>', 'Install in specific directory')
  .option('-b, --branch <branch>', 'Use specific branch (not implemented)')
  .option('-q, --quiet', 'Suppress output (for CI/CD)')
  .option('--dry-run', 'Preview actions without executing')
  .option('--include-package', 'Also copy package.json')
  .action(initCommand);

// Update command
program
  .command('update')
  .description('Update to the latest version')
  .option('-f, --force', 'Force update')
  .option('-q, --quiet', 'Suppress output')
  .action(updateCommand);

// Status command
program
  .command('status')
  .description('Check installation status')
  .action(statusCommand);

// Status command
program
  .command('status')
  .description('Check installation status')
  .action(statusCommand);

// ============================================================
// HERMÈS COMMANDS — Injection du système mémoire unifié
// ============================================================

const hermesDir = path.join(agentDir, 'hermes');

async function hermesInitCommand(options) {
  console.log(chalk.magenta.bold('🏛️  Hermès Integration — Hephaistos-Kit'));
  console.log('');

  const targetDir = options.path || process.cwd();

  if (options.dryRun) {
    console.log(chalk.yellow('🔍 DRY RUN MODE - No files will be created'));
    console.log('');
    console.log(`Source: ${hermesDir}`);
    console.log(`Target: ${targetDir}`);
    console.log(`DbRoot : ${options.dbRoot || process.env.HEPHAISTOS_DATA_DIR || path.join(os.homedir(), '.hephaistos', 'data')}`);
    console.log(`ProjectId: ${options.projectId || path.basename(targetDir)}`);
    return;
  }

  if (!await fs.pathExists(hermesDir)) {
    console.log(chalk.red('❌ .agent/hermes/ directory not found in package'));
    console.log(chalk.yellow('   Run from within Hephaistos-Kit root, or specify the package path.'));
    process.exit(1);
  }

  const projectRoot = targetDir;
  const agentHermesTarget = path.join(projectRoot, '.agent', 'hermes');
  const memoryDbDir = path.join(projectRoot, 'memory-database');
  const dbRoot = options.dbRoot || process.env.HEPHAISTOS_DATA_DIR || path.join(os.homedir(), '.hephaistos', 'data');
  const projectId = options.projectId || path.basename(targetDir);
  const projectWorkspace = path.join(dbRoot, 'current_workspace', projectId);

  console.log(`Target: ${projectRoot}`);
  console.log(`ProjectId: ${projectId}`);
  console.log(`DbRoot: ${dbRoot}`);
  console.log('');

  let success = true;

  // 1. Créer la structure de stockage locale
  console.log(chalk.cyan('[1/5] Structure de stockage locale...'));
  const localDirs = [
    path.join(memoryDbDir, 'agentmemory'),
    path.join(memoryDbDir, 'graph'),
    path.join(memoryDbDir, 'vector'),
    path.join(memoryDbDir, 'cache'),
  ];
  for (const d of localDirs) {
    if (!await fs.pathExists(d)) {
      await fs.ensureDir(d);
      if (!options.quiet) console.log(`  + ${d}`);
    }
  }

  // 2. Créer le workspace global + junction
  console.log(chalk.cyan("[2/5] Junction stockage global..."));
  if (!await fs.pathExists(projectWorkspace)) {
    await fs.ensureDir(projectWorkspace);
    if (!options.quiet) console.log(`  + ${projectWorkspace} (créé)`);
  }
  // Sous-dossiers globaux
  for (const sub of ['cache', 'graph', 'vector', 'vector/zvec-data']) {
    const gd = path.join(projectWorkspace, sub);
    if (!await fs.pathExists(gd)) await fs.ensureDir(gd);
  }
  // Junction locale -> global
  if (!await fs.pathExists(memoryDbDir)) {
    // Sur Windows, junction ; sur Unix, symlink
    if (process.platform === 'win32') {
      await fs.mkdir(memoryDbDir, { junction: projectWorkspace });
    } else {
      await fs.symlink(projectWorkspace, memoryDbDir, 'directory');
    }
    if (!options.quiet) console.log(`  ~ memory-database -> ${projectWorkspace}`);
  } else {
    if (!options.quiet) console.log(`  ~ memory-database déjà existant (skip)`);
  }

  // 3. Copier la couche hermes/ (.agent/hermes/)
  console.log(chalk.cyan("[3/5] Couche d'intégration Hermès..."));
  if (await fs.pathExists(agentHermesTarget) && !options.force) {
    console.log(chalk.yellow(`  ⚠ .agent/hermes/ déjà existant. Utilisez --force pour écraser.`));
  } else {
    if (await fs.pathExists(agentHermesTarget) && options.force) {
      await fs.remove(agentHermesTarget);
    }
    await fs.copy(hermesDir, agentHermesTarget, {
      filter: (src) => {
        const rel = path.relative(hermesDir, src);
        // On copie tout, mais on exclut test_hermès_injection.py et CHANGELOG_LAYER.md du package source
        if (rel === 'test_hermès_injection.py') return false;
        if (rel === 'CHANGELOG_LAYER.md') return false;
        if (rel.startsWith('__pycache__')) return false;
        return true;
      }
    });
    if (!options.quiet) console.log(`  + .agent/hermes/ copié`);
  }

  // 4. Créer/updater .env
  console.log(chalk.cyan("[4/5] Variable d'environnement (.env)..."));
  const envFile = path.join(projectRoot, '.env');
  if (!await fs.pathExists(envFile)) {
    const envContent = `# Hephaistos-Kit / Hermès — Configuration mémoire unifiée\n# Autorisé: modification, ajout de clés.\n# Ne pas committer les secrets.\n\nAGENT_DB_ROOT=${dbRoot}\nPROJECT_ID=${projectId}\n`;
    await fs.writeFile(envFile, envContent, 'utf8');
    if (!options.quiet) console.log(`  + .env créé`);
  } else {
    const envContent = await fs.readFile(envFile, 'utf8');
    if (!envContent.match(/^AGENT_DB_ROOT=/m)) {
      await fs.appendFile(envFile, `\nAGENT_DB_ROOT=${dbRoot}\n`, 'utf8');
      if (!options.quiet) console.log(`  ~ AGENT_DB_ROOT ajouté`);
    } else {
      if (!options.quiet) console.log(`  ~ .env déjà configuré`);
    }
  }

  // 5. Créer AGENTS.md si absent
  console.log(chalk.cyan('[5/5] Fichier AGENTS.md (règles projet)...'));
  const agentsMdPath = path.join(projectRoot, 'AGENTS.md');
  if (!await fs.pathExists(agentsMdPath)) {
    const agentsMd = await fs.readFile(path.join(hermesDir, 'templates', 'AGENTS.md'), 'utf8');
    await fs.writeFile(agentsMdPath, agentsMd, 'utf8');
    if (!options.quiet) console.log(`  + AGENTS.md créé (template)`);
  } else {
    if (!options.quiet) console.log(`  ~ AGENTS.md déjà existant (skip)`);
  }

  console.log('');
  if (success) {
    console.log(chalk.magenta.bold('✅ Hermès integration completed!'));
    if (!options.quiet) {
      console.log('');
      console.log(chalk.gray('Ce qui a été créé :'));
      console.log(chalk.gray('  .env                       ← AGENT_DB_ROOT + PROJECT_ID'));
      console.log(chalk.gray('  AGENTS.md                  ← Règles projet (template)'));
      console.log(chalk.gray('  .agent/hermes/            ← Couche d\'intégration Hermès'));
      console.log(chalk.gray('  memory-database/           ← Structure de stockage locale'));
      console.log('');
      console.log(chalk.gray('Prochaines étapes :'));
      console.log(chalk.gray('  1. Redémarrer Hermès pour charger les fichiers'));
      console.log(chalk.gray('  2. Tester la mémoire : mcp_Memory_search_nodes'));
      console.log(chalk.gray('  3. Adapter les fichiers si nécessaire'));
    }
  } else {
    console.log(chalk.red.bold('❌ Hermès integration failed'));
    process.exit(1);
  }
}

async function hermesUpdateCommand(options) {
  console.log(chalk.magenta.bold('🔄 Hermès Update — Hephaistos-Kit'));
  await hermesInitCommand({ ...options, force: true });
}

async function hermesStatusCommand(options) {
  console.log(chalk.magenta.bold('📊 Hermès Status — Hephaistos-Kit'));
  console.log('');

  const currentDir = process.cwd();
  const agentHermesPath = path.join(currentDir, '.agent', 'hermes');
  const agentsMdPath = path.join(currentDir, 'AGENTS.md');
  const envPath = path.join(currentDir, '.env');
  const memoryDbPath = path.join(currentDir, 'memory-database');

  console.log(`Current directory: ${currentDir}`);
  console.log('');

  const checks = [
    { label: '.agent/hermes/', path: agentHermesPath, description: 'Couche d\'intégration Hermès' },
    { label: 'AGENTS.md', path: agentsMdPath, description: 'Règles projet' },
    { label: '.env', path: envPath, description: 'Configuration AGENT_DB_ROOT' },
    { label: 'memory-database/', path: memoryDbPath, description: 'Stockage local' },
  ];

  for (const c of checks) {
    const exists = await fs.pathExists(c.path);
    console.log(`  ${c.label} ${exists ? chalk.green('✅') : chalk.red('❌')} — ${c.description}`);
  }

  // Vérifier la junction si memory-database existe
  if (await fs.pathExists(memoryDbPath)) {
    try {
      const stat = await fs.stat(memoryDbPath);
      if (stat.isSymbolicLink() || stat.isJunction) {
        const target = stat.target || '(junction)';
        console.log(`  Junction: ${chalk.cyan(target)}`);
      }
    } catch (e) {
      // lecture de junction échoue parfois, on ignore
    }
  }

  // Lire AGENT_DB_ROOT depuis .env si présent
  if (await fs.pathExists(envPath)) {
    try {
      const envContent = await fs.readFile(envPath, 'utf8');
      const match = envContent.match(/^AGENT_DB_ROOT=(.+)$/m);
      if (match) {
        console.log(`  AGENT_DB_ROOT: ${chalk.cyan(match[1].trim())}`);
      }
    } catch (e) { /* ignore */ }
  }
}

// Hermès command group
program
  .command('hermes')
  .description('Hermès integration commands')
  .addCommand(
    new Command('init')
      .description('Inject Hermès integration layer into a project')
      .option('-f, --force', 'Overwrite existing .agent/hermes/ directory')
      .option('-p, --path <path>', 'Target project directory (default: cwd)')
      .option('--db-root <path>', 'Global storage root (default: $HEPHAISTOS_DATA_DIR ou ~/.hephaistos/data)')
      .option('--project-id <id>', 'Project ID for memory isolation (default: directory name)')
      .option('-q, --quiet', 'Suppress output')
      .option('--dry-run', 'Preview actions without executing')
      .action(hermesInitCommand)
  )
  .addCommand(
    new Command('update')
      .description('Update Hermès integration to latest version')
      .option('-f, --force', 'Force update')
      .option('-p, --path <path>', 'Target project directory')
      .option('-q, --quiet', 'Suppress output')
      .action(hermesUpdateCommand)
  )
  .addCommand(
    new Command('status')
      .description('Check Hermès integration status in current project')
      .action(hermesStatusCommand)
  );

// Parse arguments
program.parse();
