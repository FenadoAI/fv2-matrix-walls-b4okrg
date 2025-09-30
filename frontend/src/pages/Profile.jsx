import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { toast } from "sonner";
import { LogOut, Users } from "lucide-react";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8001";
const API = `${API_BASE}/api`;

export default function Profile() {
  const { username } = useParams();
  const navigate = useNavigate();
  const [posts, setPosts] = useState([]);
  const [newPost, setNewPost] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingPosts, setLoadingPosts] = useState(true);

  const currentUser = localStorage.getItem("username");
  const token = localStorage.getItem("token");
  const isOwnProfile = currentUser === username;

  useEffect(() => {
    if (!token) {
      navigate("/");
      return;
    }
    loadPosts();
  }, [username, token]);

  const loadPosts = async () => {
    try {
      setLoadingPosts(true);
      const response = await axios.get(`${API}/posts/${username}`);
      setPosts(response.data);
    } catch (error) {
      toast.error("Failed to load posts");
    } finally {
      setLoadingPosts(false);
    }
  };

  const handlePostSubmit = async (e) => {
    e.preventDefault();
    if (!newPost.trim()) return;

    setLoading(true);
    try {
      await axios.post(
        `${API}/posts`,
        {
          wall_owner: username,
          content: newPost,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      toast.success("Post created");
      setNewPost("");
      loadPosts();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to create post");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    navigate("/");
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center gap-4">
            <Avatar className="w-16 h-16 matrix-avatar">
              <AvatarFallback className="matrix-avatar-text">
                {username?.[0]?.toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div>
              <h1 className="text-3xl font-bold matrix-title">{username}</h1>
              <p className="matrix-text">{isOwnProfile ? "Your Wall" : "User Wall"}</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => navigate("/users")}
              variant="outline"
              className="matrix-button-secondary"
            >
              <Users className="w-4 h-4 mr-2" />
              Users
            </Button>
            {isOwnProfile && (
              <Button onClick={handleLogout} variant="outline" className="matrix-button-secondary">
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </Button>
            )}
          </div>
        </div>

        {/* Post Form */}
        <Card className="mb-6 matrix-card">
          <CardHeader>
            <CardTitle className="matrix-title">
              {isOwnProfile ? "Post a Status" : `Write on ${username}'s Wall`}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handlePostSubmit} className="space-y-4">
              <Textarea
                placeholder={
                  isOwnProfile
                    ? "What's on your mind in the Matrix?"
                    : `Write a message for ${username}...`
                }
                value={newPost}
                onChange={(e) => setNewPost(e.target.value)}
                className="min-h-[100px] matrix-input"
              />
              <Button type="submit" disabled={loading || !newPost.trim()} className="matrix-button">
                {loading ? "Posting..." : "Post"}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Posts List */}
        <div className="space-y-4">
          <h2 className="text-2xl font-bold matrix-title">Wall Posts</h2>
          {loadingPosts ? (
            <Card className="matrix-card">
              <CardContent className="p-6">
                <p className="matrix-text text-center">Loading posts...</p>
              </CardContent>
            </Card>
          ) : posts.length === 0 ? (
            <Card className="matrix-card">
              <CardContent className="p-6">
                <p className="matrix-text text-center">No posts yet. Be the first to post!</p>
              </CardContent>
            </Card>
          ) : (
            posts.map((post) => (
              <Card key={post.id} className="matrix-card">
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    <Avatar className="matrix-avatar">
                      <AvatarFallback className="matrix-avatar-text">
                        {post.author[0]?.toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <button
                          onClick={() => navigate(`/profile/${post.author}`)}
                          className="font-semibold matrix-title hover:underline"
                        >
                          {post.author}
                        </button>
                        {post.author !== post.wall_owner && (
                          <span className="matrix-text text-sm">
                            → posted on {post.wall_owner}'s wall
                          </span>
                        )}
                      </div>
                      <p className="matrix-text mb-2">{post.content}</p>
                      <p className="text-xs matrix-text-dim">{formatDate(post.created_at)}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  );
}