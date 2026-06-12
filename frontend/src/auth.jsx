// Contexto de autenticacion: guarda el usuario y el token en localStorage.
import { createContext, useContext, useState } from "react";
import { api } from "./api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("user");
    return raw ? JSON.parse(raw) : null;
  });

  async function login(username, password) {
    const data = await api.login(username, password);
    localStorage.setItem("token", data.access_token);
    const u = { username: data.username, name: data.name, role: data.role };
    localStorage.setItem("user", JSON.stringify(u));
    setUser(u);
    return u;
  }

  function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
