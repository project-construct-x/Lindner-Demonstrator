export class ApiError extends Error {
  readonly status: number
  readonly body: unknown

  constructor (message: string, status: number, body?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

export type RequestOptions = Omit<RequestInit, 'body'> & {
  body?: unknown
}

export class BaseService {
  constructor (protected readonly baseUrl: string) {}

  protected async request<T> (
    path: string,
    options: RequestOptions = {},
  ): Promise<T> {
    const { body, headers, ...init } = options

    const response = await fetch(`${this.baseUrl}${path}`, {
      ...init,
      headers: {
        ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
        ...headers,
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    })

    if (!response.ok) {
      throw await this.parseError(response)
    }

    if (response.status === 204) {
      return undefined as T
    }

    const text = await response.text()
    if (!text) {
      return undefined as T
    }

    return JSON.parse(text) as T
  }

  protected get<T> (
    path: string,
    options?: Omit<RequestOptions, 'method' | 'body'>,
  ): Promise<T> {
    return this.request<T>(path, { ...options, method: 'GET' })
  }

  protected post<T> (
    path: string,
    body?: unknown,
    options?: Omit<RequestOptions, 'method' | 'body'>,
  ): Promise<T> {
    return this.request<T>(path, { ...options, method: 'POST', body })
  }

  protected put<T> (
    path: string,
    body?: unknown,
    options?: Omit<RequestOptions, 'method' | 'body'>,
  ): Promise<T> {
    return this.request<T>(path, { ...options, method: 'PUT', body })
  }

  protected patch<T> (
    path: string,
    body?: unknown,
    options?: Omit<RequestOptions, 'method' | 'body'>,
  ): Promise<T> {
    return this.request<T>(path, { ...options, method: 'PATCH', body })
  }

  protected delete<T> (
    path: string,
    options?: Omit<RequestOptions, 'method' | 'body'>,
  ): Promise<T> {
    return this.request<T>(path, { ...options, method: 'DELETE' })
  }

  private async parseError (response: Response): Promise<ApiError> {
    const text = await response.text()
    let message = text
    let body: unknown = text

    try {
      const json = JSON.parse(text) as { detail?: string | Array<{ msg: string }> }
      body = json

      if (typeof json.detail === 'string') {
        message = json.detail
      } else if (Array.isArray(json.detail)) {
        message = json.detail.map(entry => entry.msg).join(', ')
      }
    } catch {
      // keep raw text
    }

    return new ApiError(
      message || `Request failed (${response.status})`,
      response.status,
      body,
    )
  }
}
