import type { components } from "@/lib/api-types";

type Me = components["schemas"]["MeOut"] | null | undefined;

export function roleIds(me: Me) {
  return new Set(me?.roles.map((role) => role.id) || []);
}

export function isOwner(me: Me) {
  return roleIds(me).has("super_admin");
}

export function isSupport(me: Me) {
  const ids = roleIds(me);
  return ids.has("support") && !ids.has("admin") && !ids.has("super_admin");
}

export function staffLabel(me: Me) {
  if (isOwner(me)) return "Owner Console";
  if (isSupport(me)) return "Support Console";
  return "Staff Console";
}
