import { ControlRoomShell } from "@/components/control-room-shell";
import { publicProfile } from "@/lib/public-profile";

export default function HomePage() {
  return <ControlRoomShell profile={publicProfile} />;
}
