"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const config = {
    coverageProvider: "v8",
    moduleDirectories: [
        "node_modules",
        "./src"
    ],
    preset: 'ts-jest',
    rootDir: './src',
};
exports.default = config;
