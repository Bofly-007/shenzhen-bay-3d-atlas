'use strict';

const { contextBridge } = require('electron');

try {
  contextBridge.exposeInMainWorld('SZ3D_PLATFORM', 'desktop');
} catch (error) {
  window.SZ3D_PLATFORM = 'desktop';
}
