import { tryParseInt } from "utils/parse"

export const HTTP_PORT = tryParseInt(process.env.HTTP_PORT ?? '', 10, 40);
export const WS_PORT = tryParseInt(process.env.WS_PORT ?? '', 10, 8080);
export const JWT_SECRET = process.env.JWT_SECRET ?? '';