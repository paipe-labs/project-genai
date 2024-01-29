import { tryParseBoolean, tryParseInt } from "utils/parse"

export const HTTP_WS_PORT = tryParseInt(process.env.HTTP_PORT ?? '', 10, 8080);

export const ENFORCE_JWT_AUTH = tryParseBoolean(process.env.ENFORCE_JWT_AUTH ?? true);
export const JWT_SECRET = process.env.JWT_SECRET ?? '';