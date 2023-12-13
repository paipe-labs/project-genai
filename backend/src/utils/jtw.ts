import { JWT_SECRET } from 'constants/env'
import jwt from 'jsonwebtoken'

export const jwtVerify = (accessToken: string) => {
  return jwt.verify(accessToken, JWT_SECRET, { complete: false })
}