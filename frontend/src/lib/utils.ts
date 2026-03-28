export function cn(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

export function formatScore(score: number) {
  return `${score.toFixed(1)}/10`;
}

