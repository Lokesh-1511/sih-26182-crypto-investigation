// frontend/src/test/setup.ts
import '@testing-library/jest-dom';

// Polyfill ResizeObserver for jsdom
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
(globalThis as any).ResizeObserver = ResizeObserverMock;

// Polyfill HTMLCanvasElement 2D context for Cytoscape in jsdom
if (typeof HTMLCanvasElement !== 'undefined') {
  HTMLCanvasElement.prototype.getContext = function (type: string) {
    if (type === '2d') {
      return {
        fillRect: () => {},
        clearRect: () => {},
        getImageData: (_x: number, _y: number, w: number, h: number) => ({
          data: new Array(w * h * 4)
        }),
        putImageData: () => {},
        createImageData: () => [],
        setTransform: () => {},
        drawImage: () => {},
        save: () => {},
        fillText: () => {},
        restore: () => {},
        beginPath: () => {},
        moveTo: () => {},
        lineTo: () => {},
        closePath: () => {},
        stroke: () => {},
        translate: () => {},
        scale: () => {},
        rotate: () => {},
        arc: () => {},
        arcTo: () => {},
        quadraticCurveTo: () => {},
        bezierCurveTo: () => {},
        fill: () => {},
        measureText: () => ({ width: 0, actualBoundingBoxAscent: 0, actualBoundingBoxDescent: 0 }),
        transform: () => {},
        rect: () => {},
        clip: () => {},
        isPointInPath: () => false,
        createLinearGradient: () => ({ addColorStop: () => {} }),
        createRadialGradient: () => ({ addColorStop: () => {} }),
        createPattern: () => null
      } as any;
    }
    return null;
  } as any;
}

// Mock Clipboard
Object.assign(navigator, {
  clipboard: {
    writeText: async () => Promise.resolve()
  }
});
