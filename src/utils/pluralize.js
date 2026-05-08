export function pluralizeRu(count, one, few, many) {
  const mod100 = count % 100
  const mod10 = count % 10

  if (mod100 >= 11 && mod100 <= 14) return many
  if (mod10 === 1) return one
  if (mod10 >= 2 && mod10 <= 4) return few
  return many
}

export function formatCountRu(count, one, few, many) {
  return `${count} ${pluralizeRu(count, one, few, many)}`
}
