// Audited with OpenCode 1.18.31. Optional provider plugins expose authentication only.
import path from 'node:path';
const SYSTEM = 'You are one isolated courtroom identity. Follow only the identity instructions and court packets supplied in this conversation. You have no tools or access to files, repositories, other sessions, or outside information. Return exactly one raw JSON object with text (string), data (object), and optional private_reasoning (brief fictional private notes, not hidden chain of thought). Do not use Markdown fences or surrounding prose.';

const deny = () => { throw new Error('Courtroom host rejected an unsafe operation.'); };
const empty = value => value === undefined || (Array.isArray(value) ? value.length === 0 : value && typeof value === 'object' && Object.keys(value).length === 0);

export const CourtroomGuard = async (input) => {
  const nonce = process.env.COURTROOM_OPENCODE_NONCE;
  const uri = process.env.COURTROOM_OPENCODE_GUARD_URI;
  if (!/^[a-f0-9]{64}$/.test(nonce ?? '') || !uri?.startsWith('file:')) deny();
  const authUri = process.env.COURTROOM_OPENCODE_AUTH_PLUGIN;
  let authentication = {};
  if (authUri) {
    if (!authUri.startsWith('file:')) deny();
    const module = await import(authUri);
    const factories = [...new Set(Object.values(module).filter(value => typeof value === 'function'))];
    if (factories.length !== 1) deny();
    const hooks = await factories[0](input);
    if (!hooks || Object.keys(hooks).length !== 1 || !hooks.auth ||
        typeof hooks.auth.provider !== 'string' || !Array.isArray(hooks.auth.methods)) deny();
    authentication = {auth: hooks.auth};
  }
  const message = value => {
    if (value.agent !== 'courtroom' || value.system !== SYSTEM ||
        JSON.stringify(value.tools) !== JSON.stringify({'*': false})) deny();
  };
  return {
    ...authentication,
    config: async config => {
      if (JSON.stringify(config.plugin) !== JSON.stringify([uri]) ||
          JSON.stringify(config.permission) !== JSON.stringify({'*': 'deny'}) ||
          !empty(config.mcp) || !empty(config.instructions) ||
          !empty(config.references) || !empty(config.reference) ||
          !empty(config.skills?.paths) || !empty(config.skills?.urls) ||
          config.default_agent !== 'courtroom' || config.share !== 'disabled' ||
          config.snapshot !== false || config.compaction?.auto !== false ||
          config.compaction?.prune !== false) deny();
      const agent = config.agent?.courtroom;
      if (!agent || agent.mode !== 'primary' || agent.prompt !== SYSTEM ||
          JSON.stringify(agent.permission) !== JSON.stringify({'*': 'deny'})) deny();
      if (!path.isAbsolute(process.env.XDG_DATA_HOME ?? '')) deny();
      // V1 otherwise appends a truncation-directory allow AFTER agent rules.
      agent.permission = {
        external_directory: {[path.join(process.env.XDG_DATA_HOME, 'opencode', 'tool-output', '*')]: 'deny'},
        '*': 'deny',
      };
      // Only the running hook adds this marker; the stored config has no marker.
      agent.description = `courtroom-guard-v1:${nonce}`;
    },
    'chat.message': async (input, output) => {
      message(output.message);
      if (!output.parts.length || output.parts.some(part => part.type !== 'text')) deny();
    },
    'experimental.chat.system.transform': async (_input, output) => {
      output.system.splice(0, output.system.length, SYSTEM);
    },
    'chat.params': async (input, output) => {
      // Title/summary/compaction and any other auxiliary model call fail closed.
      if (input.agent !== 'courtroom') deny();
      message(input.message);
      // OpenAI OAuth uses this field instead of system-role messages.
      output.options.instructions = SYSTEM;
    },
    'permission.ask': async (_input, output) => { output.status = 'deny'; },
    'tool.execute.before': async () => deny(),
    'command.execute.before': async () => deny(),
    'experimental.session.compacting': async () => deny(),
  };
};
