import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8001";
const API = `${API_BASE}/api`;

export default function Login() {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const endpoint = isLogin ? "/login" : "/register";
      const response = await axios.post(`${API}${endpoint}`, {
        username,
        password,
      });

      localStorage.setItem("token", response.data.access_token);
      localStorage.setItem("username", response.data.user.username);

      toast.success(isLogin ? "Welcome back to the Matrix" : "Welcome to the Matrix");
      navigate(`/profile/${response.data.user.username}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md matrix-card">
        <CardHeader className="space-y-1">
          <CardTitle className="text-3xl text-center matrix-title">The Matrix</CardTitle>
          <CardDescription className="text-center matrix-text">
            {isLogin ? "Enter the Matrix" : "Join the Matrix"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username" className="matrix-text">
                Username
              </Label>
              <Input
                id="username"
                type="text"
                placeholder="neo"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="matrix-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="matrix-text">
                Password
              </Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="matrix-input"
              />
            </div>
            <Button type="submit" className="w-full matrix-button" disabled={loading}>
              {loading ? "Loading..." : isLogin ? "Enter" : "Register"}
            </Button>
          </form>
          <div className="mt-4 text-center">
            <button
              type="button"
              onClick={() => setIsLogin(!isLogin)}
              className="text-sm matrix-text hover:underline"
            >
              {isLogin ? "Don't have an account? Register" : "Already have an account? Login"}
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}