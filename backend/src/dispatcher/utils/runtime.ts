/** Runtime tests and asserts */

import { logger } from "./logger"

export const warnIf = (condition: boolean, ...data: any[]): condition is true => {
  if (condition) logger.warn(...data);
  return condition;
}