import yn from 'yn';

export const tryParseInt = (str: string, radix: number | undefined, fallback: number) => {
  const n = parseInt(str, radix);
  return isNaN(n) ? fallback : n;
}

export const tryParseBoolean = (str: string | boolean) => {
  return yn(str);
}
