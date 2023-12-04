import { tryParseInt } from "utils/parse"

export const HTTP_WS_PORT = tryParseInt(process.env.HTTP_PORT ?? '', 10, 8080);
export const JWT_SECRET = process.env.JWT_SECRET ?? '';