import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import MatrixRain from "@/components/MatrixRain";
import Login from "@/pages/Login";
import Profile from "@/pages/Profile";
import Users from "@/pages/Users";

function App() {
  return (
    <div className="App relative">
      <MatrixRain />
      <div className="relative z-10">
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Login />} />
            <Route path="/profile/:username" element={<Profile />} />
            <Route path="/users" element={<Users />} />
          </Routes>
        </BrowserRouter>
      </div>
      <Toaster position="top-right" />
    </div>
  );
}

export default App;
