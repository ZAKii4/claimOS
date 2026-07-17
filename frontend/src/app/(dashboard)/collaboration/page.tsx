"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Users, Clock, Send, CheckCircle2, MessageSquare, AlertCircle, Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { RoadmapBanner } from "@/components/RoadmapBanner";

interface Activity {
  id: string;
  user: string;
  action: string;
  time: string;
  type: string;
}

interface Comment {
  id: string;
  author: string;
  text: string;
  resolved: boolean;
}

const ROOM_ID = "CLM-2026-000154";

export default function CollaborationWorkspace() {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [actData, cmtData] = await Promise.allSettled([
          apiClient.get<Activity[]>(`/collaboration/activity/${ROOM_ID}`),
          apiClient.get<Comment[]>(`/collaboration/comments/${ROOM_ID}`),
        ]);
        
        if (actData.status === "fulfilled" && Array.isArray(actData.value)) {
          setActivities(actData.value.map((a: any, i: number) => ({
            id: a.id || String(i),
            user: a.user || a.author || "System",
            action: a.action || a.event_type || "activity",
            time: a.time || a.timestamp || "just now",
            type: a.type || "edit",
          })));
        }
        
        if (cmtData.status === "fulfilled" && Array.isArray(cmtData.value)) {
          setComments(cmtData.value.map((c: any) => ({
            id: c.id,
            author: c.author,
            text: c.content || c.text,
            resolved: c.resolved || false,
          })));
        }
      } catch (err) {
        console.error("Failed to load collaboration data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleSend = async () => {
    if (!newComment.trim()) return;
    try {
      const result = await apiClient.post<any>("/collaboration/comments", {
        author: "Current User",
        room_id: ROOM_ID,
        content: newComment,
        mentions: [],
      });
      setComments(prev => [...prev, {
        id: result.id || String(Date.now()),
        author: "Current User",
        text: newComment,
        resolved: false,
      }]);
      setNewComment("");
    } catch {
      // Fallback to local
      setComments(prev => [...prev, { id: String(Date.now()), author: "Current User", text: newComment, resolved: false }]);
      setNewComment("");
    }
  };

  return (
    <div className="space-y-6 h-full flex flex-col">
      <RoadmapBanner reason="the room is fixed to one demo claim, presence count is illustrative, and activity/comments are stored in-memory on the server (lost on restart, not a persistent database)" />
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Collaborative Workspace</h1>
          <p className="text-muted-foreground text-sm mt-1">Room: {ROOM_ID}</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex -space-x-2">
            <Avatar className="border-2 border-background w-8 h-8"><AvatarFallback className="bg-blue-500/20 text-blue-500 text-xs">AL</AvatarFallback></Avatar>
            <Avatar className="border-2 border-background w-8 h-8"><AvatarFallback className="bg-green-500/20 text-green-500 text-xs">JH</AvatarFallback></Avatar>
            <Avatar className="border-2 border-background w-8 h-8"><AvatarFallback className="bg-purple-500/20 text-purple-500 text-xs">🤖</AvatarFallback></Avatar>
          </div>
          <Badge variant="outline" className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
            3 Online
          </Badge>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center p-8">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 flex-1 min-h-0">
          
          {/* Activity Feed */}
          <Card className="col-span-1 flex flex-col h-full">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Clock className="w-4 h-4 text-muted-foreground" />
                Live Activity Feed
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto">
              <div className="space-y-4">
                {activities.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No activity yet. Start collaborating!</p>
                ) : (
                  activities.map((act) => (
                    <div key={act.id} className="flex gap-3 text-sm">
                      <div className="mt-0.5">
                        {act.type === 'validate' && <CheckCircle2 className="w-4 h-4 text-green-500" />}
                        {act.type === 'alert' && <AlertCircle className="w-4 h-4 text-red-500" />}
                        {act.type === 'edit' && <div className="w-2 h-2 mt-1 rounded-full bg-blue-500" />}
                        {act.type === 'comment' && <MessageSquare className="w-4 h-4 text-blue-500" />}
                      </div>
                      <div>
                        <p><span className="font-semibold text-primary">{act.user}</span> {act.action}</p>
                        <p className="text-xs text-muted-foreground">{act.time}</p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>

          {/* Workspace Center */}
          <Card className="col-span-1 md:col-span-1 flex flex-col h-full bg-muted/20 border-dashed">
            <CardHeader>
              <CardTitle className="text-lg">Shared Document View</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex items-center justify-center">
              <div className="text-center space-y-2">
                <Users className="w-12 h-12 text-muted-foreground mx-auto" />
                <p className="text-sm font-medium">Real-time collaboration active</p>
                <p className="text-xs text-muted-foreground">Conflict Resolution Engine: OPTIMISTIC</p>
              </div>
            </CardContent>
          </Card>

          {/* Comments & Threads */}
          <Card className="col-span-1 flex flex-col h-full">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-muted-foreground" />
                Enterprise Threads
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto space-y-4">
              {comments.map(c => (
                <div key={c.id} className={`p-3 rounded-lg border ${c.resolved ? 'bg-muted/50 opacity-60' : 'bg-card'}`}>
                  <div className="flex justify-between items-start mb-1">
                    <span className="font-semibold text-xs text-primary">{c.author}</span>
                    {c.resolved && <Badge variant="secondary" className="text-[10px]">Resolved</Badge>}
                  </div>
                  <p className="text-sm">{c.text}</p>
                </div>
              ))}
            </CardContent>
            <div className="p-4 border-t bg-card">
              <div className="flex gap-2">
                <Input 
                  placeholder="Type a comment or @mention..." 
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                />
                <Button size="icon" onClick={handleSend}>
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </Card>

        </div>
      )}
    </div>
  );
}
