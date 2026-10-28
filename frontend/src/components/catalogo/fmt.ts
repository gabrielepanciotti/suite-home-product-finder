// Formattazione numerica italiana, condivisa da griglia e tabella del catalogo.

export function eur(x: number): string {
  return x.toFixed(2).replace(".", ",");
}

export function eurPerLitro(x: number | null): string {
  return x == null ? "—" : `${x.toFixed(2).replace(".", ",")} €/L`;
}

export function num(x: number): string {
  return String(x).replace(".", ",");
}

/** "39×29×26" — ultimo numero sempre l'altezza, come nelle schede del vault. */
export function dim(a: number, b: number, h: number): string {
  return `${num(a)}×${num(b)}×${num(h)}`;
}
