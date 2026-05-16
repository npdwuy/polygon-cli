import crypto from 'crypto';
import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

const POLYGON_API_URL = 'https://polygon.codeforces.com/api';

export interface PolygonResponse<T> {
  status: 'OK' | 'FAILED';
  result?: T;
  comment?: string;
}

export class PolygonAPI {
  private apiKey: string;
  private apiSecret: string;

  constructor() {
    this.apiKey = process.env.POLYGON_API_KEY || '';
    this.apiSecret = process.env.POLYGON_API_SECRET || '';

    if (!this.apiKey || !this.apiSecret) {
      throw new Error('POLYGON_API_KEY and POLYGON_API_SECRET must be set in .env');
    }
  }

  /**
   * Generates apiSig for Polygon API requests
   */
  private generateSignature(methodName: string, params: Record<string, any>): string {
    const rand = Math.random().toString(36).substring(2, 8);
    const time = Math.floor(Date.now() / 1000).toString();

    // Add apiKey and time to params
    const allParams = { ...params, apiKey: this.apiKey, time };

    // Create a list of [key, value] pairs and sort them
    // Polygon requires sorting lexicographically by key, then by value
    const paramPairs: [string, string][] = [];
    for (const [key, value] of Object.entries(allParams)) {
      if (Array.isArray(value)) {
        value.forEach(v => paramPairs.push([key, String(v)]));
      } else {
        paramPairs.push([key, String(value)]);
      }
    }

    paramPairs.sort((a, b) => {
      if (a[0] !== b[0]) return a[0].localeCompare(b[0]);
      return a[1].localeCompare(b[1]);
    });

    const queryString = paramPairs
      .map(([key, value]) => `${key}=${value}`)
      .join('&');

    const sigBase = `${rand}/${methodName}?${queryString}#${this.apiSecret}`;
    const hash = crypto.createHash('sha512').update(sigBase).digest('hex');

    return rand + hash;
  }

  /**
   * Calls a Polygon API method with retry logic for rate limits
   */
  async call<T>(methodName: string, params: Record<string, any> = {}, attempt = 0): Promise<T> {
    const time = Math.floor(Date.now() / 1000).toString();
    const apiSig = this.generateSignature(methodName, params);

    const fullParams = {
      ...params,
      apiKey: this.apiKey,
      time,
      apiSig,
    };

    try {
      const response = await axios.post<PolygonResponse<T>>(
        `${POLYGON_API_URL}/${methodName}`,
        new URLSearchParams(fullParams).toString(),
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      );

      if (response.data.status === 'FAILED') {
        throw new Error(`Polygon API Error: ${response.data.comment}`);
      }

      return response.data.result!;
    } catch (error: any) {
      // Handle Rate Limit (HTTP 429)
      if (axios.isAxiosError(error) && error.response?.status === 429 && attempt < 5) {
        const delay = Math.pow(2, attempt) * 1000;
        console.warn(`Rate limited. Retrying ${methodName} in ${delay}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.call(methodName, params, attempt + 1);
      }

      if (axios.isAxiosError(error) && error.response?.data) {
        const data = error.response.data as PolygonResponse<any>;
        throw new Error(`Polygon API ${methodName} failed: ${data.comment || error.message}`);
      }
      throw error;
    }
  }
  /**
   * Downloads a file from Polygon API (e.g., problem package)
   */
  async download(methodName: string, params: Record<string, any> = {}, attempt = 0): Promise<Buffer> {
    const time = Math.floor(Date.now() / 1000).toString();
    const apiSig = this.generateSignature(methodName, params);

    const fullParams = {
      ...params,
      apiKey: this.apiKey,
      time,
      apiSig,
    };

    try {
      const response = await axios.post(
        `${POLYGON_API_URL}/${methodName}`,
        new URLSearchParams(fullParams).toString(),
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          responseType: 'arraybuffer',
        }
      );

      // Check if the response is actually a JSON error (status failed)
      // ArrayBuffer can be converted to string to check for "status":"FAILED"
      if (String(response.headers['content-type']).includes('application/json')) {
          const json = JSON.parse(Buffer.from(response.data).toString());
          if (json.status === 'FAILED') {
              throw new Error(`Polygon API Error: ${json.comment}`);
          }
      }

      return Buffer.from(response.data);
    } catch (error: any) {
      if (axios.isAxiosError(error) && error.response?.status === 429 && attempt < 5) {
        const delay = Math.pow(2, attempt) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.download(methodName, params, attempt + 1);
      }
      throw error;
    }
  }
}
