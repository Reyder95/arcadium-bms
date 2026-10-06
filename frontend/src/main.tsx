import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from "react-router"

import "@fontsource/sanchez"

import "./index.css"
import HomePage from './HomePage.tsx'
import Layout from './Layout.tsx'
import { AuthProvider } from './hooks/useAuth.tsx'
import Login from './Pages/Login.tsx'
import RequireAuth from './Components/General/RequireAuth.tsx'
import Register from './Pages/Register.tsx'

const router = createBrowserRouter([
  {
    path: "/login", element: <Login />
  },
  {
    path: "/register", element: <Register />
  },
  {
    path: "/",
    element: <Layout />,
    children: [
      {
        element: <RequireAuth />,
        children: [
          { index: true, element: <HomePage />}
        ]
      }

    ]
  }
])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <RouterProvider router={router}/>
    </AuthProvider>
  </StrictMode>,
)
