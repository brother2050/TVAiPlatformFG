/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare module 'wavesurfer.js' {
  const WaveSurfer: any
  export default WaveSurfer
}

declare module 'fabric' {
  export const fabric: any
}
