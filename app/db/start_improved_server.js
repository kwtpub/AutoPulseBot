/**
 * Auto-restart Server Launcher - автоматический перезапуск при критических ошибках
 * Мониторинг health check и автоматическое восстановление сервера
 */

const { spawn } = require('child_process');
const http = require('http');
const path = require('path');

class ServerLauncher {
  constructor() {
    this.serverProcess = null;
    this.restartCount = 0;
    this.maxRestarts = 10;
    this.restartDelay = 5000; // 5 секунд
    this.healthCheckInterval = 30000; // 30 секунд
    this.healthCheckTimeout = 10000; // 10 секунд
    this.port = process.env.NODE_PORT || 3001;
    this.isShuttingDown = false;
    
    this.setupSignalHandlers();
    this.startServer();
  }

  setupSignalHandlers() {
    process.on('SIGTERM', () => {
      console.log('🛑 SIGTERM received, shutting down launcher...');
      this.shutdown();
    });

    process.on('SIGINT', () => {
      console.log('🛑 SIGINT received, shutting down launcher...');
      this.shutdown();
    });
  }

  startServer() {
    if (this.isShuttingDown) return;

    console.log(`🚀 Starting server (attempt ${this.restartCount + 1})...`);
    
    const serverScript = path.join(__dirname, 'server_improved.js');
    
    this.serverProcess = spawn('node', [serverScript], {
      stdio: 'inherit',
      env: process.env
    });

    this.serverProcess.on('exit', (code, signal) => {
      if (this.isShuttingDown) return;

      console.log(`❌ Server exited with code ${code}, signal ${signal}`);
      
      if (this.restartCount < this.maxRestarts) {
        console.log(`🔄 Restarting server in ${this.restartDelay}ms...`);
        setTimeout(() => {
          this.restartCount++;
          this.startServer();
        }, this.restartDelay);
      } else {
        console.error(`🔴 Maximum restart attempts (${this.maxRestarts}) reached. Giving up.`);
        process.exit(1);
      }
    });

    this.serverProcess.on('error', (err) => {
      console.error('❌ Failed to start server process:', err);
    });

    // Начинаем health check через 10 секунд после старта
    setTimeout(() => {
      this.startHealthCheck();
    }, 10000);
  }

  startHealthCheck() {
    if (this.isShuttingDown) return;

    this.healthCheckTimer = setInterval(() => {
      this.performHealthCheck();
    }, this.healthCheckInterval);
  }

  async performHealthCheck() {
    if (this.isShuttingDown) return;

    try {
      const healthStatus = await this.checkServerHealth();
      
      if (healthStatus.healthy) {
        // Сбрасываем счетчик перезапусков при успешном health check
        this.restartCount = 0;
        
        if (healthStatus.database.connected) {
          console.log('✅ Health check passed - server and database OK');
        } else {
          console.warn('⚠️ Health check: server OK, database issues detected');
        }
      } else {
        console.error('🔴 Health check failed - server may be unresponsive');
        this.restartServer('Health check failed');
      }
      
    } catch (error) {
      console.error('❌ Health check error:', error.message);
      this.restartServer('Health check error');
    }
  }

  checkServerHealth() {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Health check timeout'));
      }, this.healthCheckTimeout);

      const options = {
        hostname: 'localhost',
        port: this.port,
        path: '/api/health',
        method: 'GET',
        timeout: this.healthCheckTimeout
      };

      const req = http.request(options, (res) => {
        clearTimeout(timeout);
        
        let data = '';
        res.on('data', (chunk) => {
          data += chunk;
        });

        res.on('end', () => {
          try {
            const healthData = JSON.parse(data);
            
            resolve({
              healthy: res.statusCode === 200,
              statusCode: res.statusCode,
              server: healthData.server,
              database: healthData.database
            });
          } catch (parseError) {
            reject(new Error('Invalid health check response'));
          }
        });
      });

      req.on('error', (error) => {
        clearTimeout(timeout);
        reject(error);
      });

      req.on('timeout', () => {
        clearTimeout(timeout);
        req.destroy();
        reject(new Error('Health check request timeout'));
      });

      req.end();
    });
  }

  restartServer(reason) {
    if (this.isShuttingDown) return;
    
    console.log(`🔄 Restarting server due to: ${reason}`);
    
    if (this.healthCheckTimer) {
      clearInterval(this.healthCheckTimer);
    }

    if (this.serverProcess) {
      console.log('🛑 Terminating current server process...');
      this.serverProcess.kill('SIGTERM');
      
      // Принудительное завершение через 10 секунд
      setTimeout(() => {
        if (this.serverProcess && !this.serverProcess.killed) {
          console.log('🔪 Force killing server process...');
          this.serverProcess.kill('SIGKILL');
        }
      }, 10000);
    }
  }

  shutdown() {
    this.isShuttingDown = true;
    
    console.log('🛑 Shutting down server launcher...');
    
    if (this.healthCheckTimer) {
      clearInterval(this.healthCheckTimer);
    }

    if (this.serverProcess) {
      console.log('🛑 Terminating server process...');
      this.serverProcess.kill('SIGTERM');
      
      setTimeout(() => {
        if (this.serverProcess && !this.serverProcess.killed) {
          console.log('🔪 Force killing server process...');
          this.serverProcess.kill('SIGKILL');
        }
        process.exit(0);
      }, 5000);
    } else {
      process.exit(0);
    }
  }
}

// Запуск launcher
console.log('🎬 Starting Server Launcher with auto-restart capabilities...');
console.log(`📊 Health checks every ${30}s, restart delay ${5}s`);
console.log(`🔄 Max restarts: ${10}`);

new ServerLauncher(); 