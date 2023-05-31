export const tryParseInt = (str: string, radix: number | undefined, fallback: number) => {
    const n = parseInt(str, radix);
    return isNaN(n) ? fallback : n;
}