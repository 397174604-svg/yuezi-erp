const fs = require('fs')
const path = require('path')

const projectRoot = path.resolve(__dirname, '../../..')
const pnpmRoot = path.join(projectRoot, 'node_modules', '.pnpm')
const vueJestPackage = fs.readdirSync(pnpmRoot).find(name => name.startsWith('vue-jest@'))

if (!vueJestPackage) throw new Error('vue-jest is not installed in node_modules/.pnpm')

module.exports = {
  rootDir: projectRoot,
  moduleFileExtensions: ['js', 'json', 'vue'],
  transform: {
    '^.+\\.vue$': path.join(pnpmRoot, vueJestPackage, 'node_modules', 'vue-jest'),
    '^.+\\.js$': require.resolve('babel-jest')
  },
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1'
  },
  testMatch: [
    '<rootDir>/tests/unit/erp/formalMenuConfigResolution.spec.js',
    '<rootDir>/tests/unit/erp/erp104RouteIntegrity.spec.js'
  ],
  testURL: 'http://localhost/'
}
