import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api } from "../api";

export default function LoginPage() {
  const nav = useNavigate();
  const [form, setForm] = useState({ username: "", password: "" });
  const [err, setErr] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    try {
      await api.login(form);
      nav("/feed");
    } catch (e) {
      setErr(e.message);
    }
  };

  return (
    <div className="auth-container">
      <h1 className="page-title">Вход</h1>
      {err && <div className="msg-error">{err}</div>}
      <div className="auth-card">
        <form onSubmit={submit}>
          <div className="form-group">
            <label className="form-label">Имя пользователя</label>
            <input className="form-input" placeholder="alice" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required />
          </div>
          <div className="form-group">
            <label className="form-label">Пароль</label>
            <input className="form-input" placeholder="Ваш пароль" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
          </div>
          <button type="submit" className="btn btn-primary btn-block">Войти</button>
        </form>
        <div className="auth-link">
          Нет аккаунта? <Link to="/register">Зарегистрироваться</Link>
        </div>
      </div>
    </div>
  );
}
