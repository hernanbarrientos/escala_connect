import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: '/',  // se for deploy na raiz do domínio
  // se for num subdiretório, base: '/subpasta/'
  build: {
    outDir: 'dist'  // ou verificar se distDir do vercel.json bate
  }
});