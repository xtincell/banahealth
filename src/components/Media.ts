/**
 * Acces aux visuels recuperes depuis les sauvegardes du site d'origine.
 * Seuls les fichiers reellement presents sont referencables : une image
 * manquante renvoie null plutot que de casser la compilation.
 */
const medias = import.meta.glob<{ default: ImageMetadata }>(
  '../assets/media/*.{jpg,jpeg,png,webp,avif}',
  { eager: true },
);

const index = new Map<string, ImageMetadata>();
for (const [chemin, mod] of Object.entries(medias)) {
  const nom = chemin.split('/').pop()!.replace(/\.[^.]+$/, '');
  index.set(nom, mod.default);
}

export function media(nom: string | undefined): ImageMetadata | null {
  if (!nom) return null;
  return index.get(nom) ?? null;
}

export function mediaDisponibles(): string[] {
  return [...index.keys()].sort();
}
