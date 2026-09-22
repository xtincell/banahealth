/// <reference types="astro/client" />

/** Les fichiers de textes sont charges tels quels par le greffon YAML. */
declare module '*.yaml' {
  const contenu: any;
  export default contenu;
}
