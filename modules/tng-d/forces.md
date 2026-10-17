# Forces — canon as intentions, not episodes

After the branch, canon does not schedule anything. What survives is the forces: who wants what, what they can do, and what they would do next if nobody stopped them. **Intentions are conserved; intersections are not.** A force meets the Enterprise only if her course, her orders and the world's causes put them in the same place.

This file is the seed. At build, each force becomes an entry in `state/forces.json` with a `default_trajectory` (canon's next steps, each with its preconditions) and a `divergence` status per step: `on_track`, `delayed`, `averted`, `altered` — every change citing the ledger entry that caused it. The world's own turn moves each force one step when its preconditions hold, whether or not the Enterprise is anywhere near.

Your foreknowledge of the show is a map of the *undisturbed* trajectory. After the first divergence it starts to lie. Acting on it is allowed; in the world it is acting on a reason nobody else can see, and people notice unexplained reasons.

| Force | State at the branch | Wants | Default trajectory (preconditions) |
|---|---|---|---|
| **Q** | [canon] Has put humanity "on trial" and let the Farpoint test stand. Omnipotent within its own rules; bored easily. | To keep watching humanity, and to provoke it. | Returns to test the crew again, more personally (when the Enterprise is somewhere quiet enough to be interesting). Later: forces contact with something humanity is not ready for (when its own patience with the crew runs out). |
| **Ferengi Alliance** | [canon] Known only by rumour. Expanding, opportunistic. | Profit; Federation technology. | First face-to-face contact through a dispute over something stolen (when a Ferengi ship and a Federation ship pursue the same object). |
| **Romulan Star Empire** | [canon] Silent since 2311. | Security; to know what is happening along the Neutral Zone. | Their outposts along the Zone are destroyed by something unknown; they come out of silence to find out who did it (once the destruction happens — see the Borg). |
| **The Borg** | [canon] Unknown to the Federation. | Assimilation. | Destroy outposts along the Neutral Zone, Federation and Romulan both, without anyone seeing who (late 2364). First face-to-face contact much later, unless something brings it forward. |
| **The infiltration** | [canon] Parasitic beings are spreading through Starfleet Command, taking officers from the inside. Captain Walker Keel and others have begun to notice. | Control of Starfleet. | Starfleet's Inspector General opens an inquiry into the Enterprise and her captain (stardate ~414xx). Keel tries to warn Picard in secret (when he can arrange a meeting away from Command). Open confrontation at Starfleet Headquarters (if nobody stops it first). |
| **Lore** | [canon] Data's disassembled older "brother", in Soong's laboratory on Omicron Theta, waiting to be found. | Whatever he wants when he wakes up; he is not who Data thinks. | Found and reassembled (if the Enterprise surveys Omicron Theta). |
| **The Crystalline Entity** | [canon] Destroyed the Omicron Theta colony in 2336. Moves between systems, consuming life. | To feed. | Not on any schedule; appears where it appears. |
| **The Traveler** | [canon] A being who uses warp experiments as a vehicle; drawn to minds like Wesley Crusher's. | To study; to find someone like himself. | Arrives with a Starfleet propulsion specialist's warp "improvements" (when the Enterprise tests experimental drive changes). |
| **Armus** | [canon] A malevolent being abandoned on Vagra II. | To hurt; to be acknowledged. | Kills whoever comes near (if anyone lands on Vagra II). |
| **Starfleet Command** | [canon] Far away; replies late; politically split over the flagship. | Results, reports, and no embarrassment. | Orders, reassignments, inspections. |
| **The Klingon Empire** | [canon] An ally. | Honour; a stable border. | Officer exchanges and diplomatic friction. |

Canon events that are no longer guaranteed, because their preconditions are now open: Wesley's field promotion, Lore's discovery, Lt. Yar's death on Vagra II, Dr. Crusher's transfer to Starfleet Medical, the Inspector General's inquiry, and the infiltration's confrontation at Headquarters. Each happens only if the world's causes produce it.

## Adding forces

A force may be added in play only if it is canon to this era or follows from the world's own causes. A new force is written into `state/forces.json` before it can be felt, and the lore audit checks it at the next stand-down.
