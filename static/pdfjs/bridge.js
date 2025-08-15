// ESM bridge to expose pdfjs API on window.pdfjsLib for our simple viewer
import * as pdfjs from '/static/pdfjs/pdf.js';

// Expose to global like the UMD build would
window.pdfjsLib = pdfjs;

// Configure worker from our static path
try {
  if (pdfjs && pdfjs.GlobalWorkerOptions) {
    pdfjs.GlobalWorkerOptions.workerSrc = '/static/pdfjs/pdf.worker.js';
  }
} catch (e) {
  console.warn('Falha ao configurar worker do PDF.js no bridge:', e);
}

