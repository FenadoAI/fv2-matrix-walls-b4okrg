import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { ArrowLeft } from "lucide-react";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8001";
const API = `${API_BASE}/api`;

export default function Users() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const currentUser = localStorage.getItem("username");

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      navigate("/");
      return;
    }
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/users`);
      setUsers(response.data);
    } catch (error) {
      toast.error("Failed to load users");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-4 mb-6">
          <Button
            onClick={() => navigate(`/profile/${currentUser}`)}
            variant="outline"
            className="matrix-button-secondary"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <h1 className="text-3xl font-bold matrix-title">Users in the Matrix</h1>
        </div>

        {loading ? (
          <Card className="matrix-card">
            <CardContent className="p-6">
              <p className="matrix-text text-center">Loading users...</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {users.map((user) => (
              <Card
                key={user.id}
                className="matrix-card cursor-pointer hover:scale-105 transition-transform"
                onClick={() => navigate(`/profile/${user.username}`)}
              >
                <CardContent className="p-6">
                  <div className="flex items-center gap-4">
                    <Avatar className="w-12 h-12 matrix-avatar">
                      <AvatarFallback className="matrix-avatar-text">
                        {user.username[0]?.toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <h3 className="font-semibold matrix-title">{user.username}</h3>
                      {user.username === currentUser && (
                        <span className="text-sm matrix-text">(You)</span>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}