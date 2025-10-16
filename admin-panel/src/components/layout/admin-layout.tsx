import { Outlet } from "react-router-dom"
import { Sidebar } from "./sidebar"
import { TopBar } from "./top-bar"

export const AdminLayout = () => {
  return (
    <div className="flex min-h-screen w-full bg-background text-foreground">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <TopBar />
        <main className="flex-1 overflow-y-auto bg-muted/20 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
