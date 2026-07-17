import Link from "next/link";
import { 
  LayoutDashboard, 
  FileText, 
  Users, 
  Settings, 
  ShieldCheck, 
  Activity, 
  Cpu, 
  Network,
  TestTube,
  BookOpen,
  Scale,
  Code2,
  Globe,
  GitGraph,
  MonitorCheck,
  Inbox
} from "lucide-react";

export function Sidebar() {
  const menuItems = [
    { name: "Executive Dashboard", href: "/", icon: LayoutDashboard },
    { name: "Claims Workspace", href: "/claims", icon: FileText },
    { name: "Live Agents Console", href: "/agents", icon: Users },
    { name: "Collaborative Workspace", href: "/collaboration", icon: Users },
    { name: "Workflow Studio", href: "/workflow", icon: Network },
    { name: "AI Laboratory", href: "/lab", icon: TestTube },
    { name: "Monitoring Center", href: "/monitoring", icon: Activity },
    { name: "Analytics Center", href: "/analytics", icon: Activity },
    { name: "Platform Operations", href: "/platform", icon: ShieldCheck },
    { name: "Executive Command Center", href: "/command-center", icon: MonitorCheck },
    { name: "Claims Overview", href: "/claims", icon: Inbox },
    { name: "Global Federation", href: "/federation", icon: Globe },
    { name: "AI Governance", href: "/governance", icon: Scale },
    { name: "Developer Center", href: "/developer", icon: Code2 },
    { name: "System Settings", href: "/settings", icon: Settings },
    { name: "Local AI Center", href: "/local-ai", icon: Cpu },
  ];

  return (
    <aside className="w-64 border-r bg-card flex flex-col h-full shadow-sm">
      <div className="h-16 flex items-center px-6 border-b font-bold text-xl tracking-tight text-primary">
        claim<span className="text-foreground">OS</span>
      </div>
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        {menuItems.map((item) => {
          const Icon = item.icon;
          return (
            <Link 
              key={item.href} 
              href={item.href}
              className="flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
            >
              <Icon className="w-4 h-4" />
              {item.name}
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t text-xs text-muted-foreground flex justify-between">
        <span>ACOS Mode</span>
        <span className="text-green-500 font-medium flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-green-500"></span> Active
        </span>
      </div>
    </aside>
  );
}
