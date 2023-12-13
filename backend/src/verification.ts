import { jwtVerify } from "utils/jtw"

export const verify = (token: string): boolean => {
  try {
    const jwt = jwtVerify(token);
    if (typeof jwt === "string") return false;
    // expiration is checked automatically
    // can check jwt['user_metadata']

    return true;
  } catch {
    return false;
  }
}