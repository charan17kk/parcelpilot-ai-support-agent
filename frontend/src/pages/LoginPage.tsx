import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight, Bot, CheckCircle2, LoaderCircle, LockKeyhole } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { api } from "../lib/api";
import { useAuthStore } from "../store/auth";

const schema = z.object({ email: z.string().email(), password: z.string().min(8) });
type LoginFields = z.infer<typeof schema>;

const demos = [
  ["Northstar customer", "northstar@demo.parcelpilot.com"],
  ["Support agent", "support@demo.parcelpilot.com"],
] as const;

export function LoginPage() {
  const setUser = useAuthStore((state) => state.setUser);
  const [serverError, setServerError] = useState("");
  const { register, handleSubmit, setValue, formState: { errors, isSubmitting } } = useForm<LoginFields>({
    resolver: zodResolver(schema),
    defaultValues: { email: "northstar@demo.parcelpilot.com", password: "ParcelPilotDemo!" },
  });

  const submit = async (values: LoginFields) => {
    setServerError("");
    try {
      const result = await api.login(values.email, values.password);
      setUser(result.user);
    } catch (reason) {
      setServerError(reason instanceof Error ? reason.message : "Unable to sign in");
    }
  };

  return (
    <main className="login-page">
      <section className="login-story">
        <div className="login-brand"><span className="brand-mark"><Bot size={21} /></span> ParcelPilot Assist</div>
        <div className="story-copy"><span className="eyebrow light">Trust-aware support AI</span><h1>Answers grounded in the rules that actually apply.</h1><p>Investigate shipments, check contract overrides, calculate credits, and escalate safely—with evidence attached.</p>
          <ul><li><CheckCircle2 /> Account-scoped operational data</li><li><CheckCircle2 /> Contract-first source precedence</li><li><CheckCircle2 /> Confirmation before every action</li></ul>
        </div>
        <p className="story-foot">Built for ParcelPilot customer operations</p>
      </section>
      <section className="login-panel">
        <form className="login-card" onSubmit={handleSubmit(submit)}>
          <span className="login-icon"><LockKeyhole /></span><span className="eyebrow">Demo access</span><h2>Welcome back</h2><p>Choose a demo identity or enter your credentials.</p>
          <div className="demo-choices">{demos.map(([label, email]) => <button type="button" key={email} onClick={() => { setValue("email", email); setValue("password", "ParcelPilotDemo!"); }}><strong>{label}</strong><small>{email}</small></button>)}</div>
          <label>Email<input {...register("email")} autoComplete="username" />{errors.email && <small className="field-error">Enter a valid email.</small>}</label>
          <label>Password<input {...register("password")} type="password" autoComplete="current-password" />{errors.password && <small className="field-error">Password is required.</small>}</label>
          {serverError && <div className="inline-error">{serverError}</div>}
          <button className="button primary login-submit" disabled={isSubmitting}>{isSubmitting ? <LoaderCircle className="spin" size={17} /> : null} Sign in <ArrowRight size={17} /></button>
          <p className="demo-note">Demo password: <code>ParcelPilotDemo!</code></p>
        </form>
      </section>
    </main>
  );
}
