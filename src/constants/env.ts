import { tryParseInt } from "utils/parse"

export const HTTP_PORT = tryParseInt(process.env.HTTP_PORT ?? '', 10, 4040);
export const WS_PORT = tryParseInt(process.env.WS_PORT ?? '', 10, 8080);