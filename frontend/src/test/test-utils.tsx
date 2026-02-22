import type { ReactElement, PropsWithChildren } from 'react'
import { render, type RenderOptions } from '@testing-library/react'
import { configureStore, combineReducers } from '@reduxjs/toolkit'
import { Provider } from 'react-redux'
import { MemoryRouter } from 'react-router-dom'
import { TooltipProvider } from '@radix-ui/react-tooltip'
import authReducer from '@/infrastructure/store/slices/authSlice'
import chatReducer from '@/infrastructure/store/slices/chatSlice'
import uploadModalReducer from '@/infrastructure/store/slices/uploadModalSlice'
import themeReducer from '@/infrastructure/store/slices/themeSlice'

const rootReducer = combineReducers({
  auth: authReducer,
  chat: chatReducer,
  uploadModal: uploadModalReducer,
  theme: themeReducer,
})

type RootState = ReturnType<typeof rootReducer>

interface ExtendedRenderOptions extends Omit<RenderOptions, 'queries'> {
  preloadedState?: Partial<RootState>
  route?: string
}

export function renderWithProviders(
  ui: ReactElement,
  {
    preloadedState = {},
    route = '/',
    ...renderOptions
  }: ExtendedRenderOptions = {}
) {
  const store = configureStore({
    reducer: rootReducer,
    preloadedState: preloadedState as any,
  })

  function Wrapper({ children }: PropsWithChildren) {
    return (
      <Provider store={store}>
        <MemoryRouter initialEntries={[route]}>
          <TooltipProvider>
            {children}
          </TooltipProvider>
        </MemoryRouter>
      </Provider>
    )
  }

  return { store, ...render(ui, { wrapper: Wrapper, ...renderOptions }) }
}

export { rootReducer }
export type { RootState }
