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
    const url = `${this.baseUrl}${path}`
    const method = init.method ?? 'GET'

    console.log('[Construct-X] [api]', `${method} ${url}`, body ?? '')

    const response = await fetch(url, {
      ...init,
      headers: {
        ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
        ...headers,
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    })

    if (!response.ok) {
      const apiError = await this.parseError(response)
      console.error('[Construct-X] [api]', `${method} ${url} failed`, {
        status: response.status,
        body: apiError.body,
      })
      throw apiError
    }

    if (response.status === 204) {
      console.log('[Construct-X] [api]', `${method} ${url} -> 204`)
      return undefined as T
    }

    const text = await response.text()
    if (!text) {
      console.log('[Construct-X] [api]', `${method} ${url} -> empty`)
      return undefined as T
    }

    const data = JSON.parse(text) as T
    console.log('[Construct-X] [api]', `${method} ${url} ->`, data)
    return data
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
