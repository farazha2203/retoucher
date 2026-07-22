export type UserRole='client'|'editor'|'support'|'supervisor'|'admin';
export interface AuthUser{id:number;username:string;email:string;first_name:string;last_name:string;role:UserRole;phone_number:string;avatar:string|null;is_verified:boolean;date_joined:string;}
export interface LoginPayload{username:string;password:string;}
export interface RegisterPayload{username:string;email:string;password:string;password_confirm:string;first_name:string;last_name:string;role:'client'|'editor';phone_number?:string;}
export interface TokenPair{access:string;refresh:string;}
export interface RefreshResponse{access:string;refresh?:string;}
export interface SocialAuthExchangeResponse extends TokenPair{user:AuthUser;redirect_to:string;}
