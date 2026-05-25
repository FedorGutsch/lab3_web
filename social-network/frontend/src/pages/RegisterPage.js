import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api } from "../api";

export default function RegisterPage() {
  const nav = useNavigate();
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [err, setErr] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    try {
      await api.register(form);
      await api.login({ username: form.username, password: form.password });
      nav("/feed");
    } catch (e) {
      setErr(e.message);
    }
  };

  return (
    <div className="auth-container">
      <h1 className="page-title">Регистрация</h1>
      {err && <div className="msg-error">{err}</div>}
      <div className="auth-card">
        <form onSubmit={submit}>
          <div className="form-group">
            <label className="form-label">Имя пользователя</label>
            <input className="form-input" placeholder="alice" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required />
          </div>
          <div className="form-group">
            <label className="form-label">Email</label>
            <input className="form-input" placeholder="alice@example.com" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          </div>
          <div className="form-group">
            <label className="form-label">Пароль</label>
            <input className="form-input" placeholder="Минимум 6 символов" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
          </div>
          <button type="submit" className="btn btn-primary btn-block">Зарегистрироваться</button>
        </form>
        <div className="auth-link">
          Уже есть аккаунт? <Link to="/login">Войти</Link>
        </div>
      </div>
    </div>
  );
}
