import type {
  PublicLink,
  PublicProfile,
  PublicProject,
} from "@/lib/public-profile";
import { SceneFailureBoundary } from "@/components/scene/scene-failure-boundary";
import { ScenePlaceholder } from "@/components/scene/scene-placeholder";

interface ControlRoomShellProps {
  profile: PublicProfile;
}

function projectLinks(
  project: PublicProject,
  links: PublicLink[],
): PublicLink[] {
  const projectLinkIds = new Set(project.linkIds);

  return links.filter((link) => projectLinkIds.has(link.id));
}

export function ControlRoomShell({
  profile,
}: ControlRoomShellProps) {
  const featuredProjects = profile.projects.filter(
    (project) => project.featured,
  );

  return (
    <>
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>

      <header className="site-header">
        <a className="site-identity" href="#profile">
          <span className="identity-mark" aria-hidden="true">
            MP
          </span>
          <span>
            <strong>{profile.displayName}</strong>
            <small>Control Room</small>
          </span>
        </a>

        <nav aria-label="Primary navigation">
          <a href="#profile">Profile</a>
          <a href="#projects">Projects</a>
          <a href="#systems">Systems</a>
          <a href="#evidence">Evidence</a>
          <a href="#contact">Contact</a>
        </nav>
      </header>

      <main id="main-content" tabIndex={-1}>
        <section className="hero" id="profile">
          <div className="hero-copy">
            <p className="eyebrow">{profile.identity.headline}</p>
            <h1>{profile.displayName}</h1>
            <p className="hero-role">{profile.identity.role}</p>
            <p className="hero-summary">{profile.identity.summary}</p>
            <blockquote>{profile.identity.motto}</blockquote>

            <div className="hero-actions">
              <a className="primary-action" href="#projects">
                Inspect featured work
              </a>
              <a className="text-action" href="#evidence">
                Review engineering evidence
              </a>
            </div>
          </div>

          <SceneFailureBoundary>
            <ScenePlaceholder />
          </SceneFailureBoundary>
        </section>

        <section className="projects-section" id="projects">
          <header className="section-heading">
            <p className="eyebrow">Featured work</p>
            <h2>Projects as engineering systems</h2>
            <p>
              Each project is positioned by its observable architecture,
              responsibilities, and verification rather than by a generic
              card template.
            </p>
          </header>

          <div className="project-sequence">
            {featuredProjects.map((project, index) => {
              const links = projectLinks(project, profile.links);

              return (
                <article
                  className="project-entry"
                  id={`project-${project.id}`}
                  key={project.id}
                >
                  <span className="project-index" aria-hidden="true">
                    {String(index + 1).padStart(2, "0")}
                  </span>

                  <div>
                    <p className="project-status">{project.status}</p>
                    <h3>{project.name}</h3>
                    <p>{project.summary}</p>
                  </div>

                  <div className="project-routes">
                    {links.length > 0 ? (
                      links.map((link) => (
                        <a
                          href={link.url}
                          key={link.id}
                          rel="noreferrer"
                          target="_blank"
                        >
                          {link.label}
                        </a>
                      ))
                    ) : (
                      <a href="#evidence">View related evidence</a>
                    )}
                  </div>
                </article>
              );
            })}
          </div>
        </section>

        <section className="systems-section" id="systems">
          <header className="section-heading">
            <p className="eyebrow">Connected practice</p>
            <h2>Engineering systems map</h2>
            <p>
              Disciplines are connected to concrete project and evidence
              identifiers. Technologies remain supporting implementation
              choices rather than the profile’s primary message.
            </p>
          </header>

          <div className="systems-layout">
            <div className="discipline-map">
              {profile.disciplines.map((discipline) => (
                <article key={discipline.id}>
                  <span aria-hidden="true" className="system-node" />
                  <div>
                    <h3>{discipline.name}</h3>
                    <p>{discipline.summary}</p>
                  </div>
                </article>
              ))}
            </div>

            <aside className="technology-register">
              <h3>Implementation evidence</h3>
              <dl>
                {profile.technologies.map((technology) => (
                  <div key={technology.id}>
                    <dt>{technology.name}</dt>
                    <dd>{technology.usage}</dd>
                  </div>
                ))}
              </dl>
            </aside>
          </div>
        </section>

        <section className="evidence-section" id="evidence">
          <header className="section-heading">
            <p className="eyebrow">Verification record</p>
            <h2>Evidence before claims</h2>
            <p>
              Each record supports a bounded statement. Repository history,
              tests, and architecture material are not inflated beyond what
              they demonstrate.
            </p>
          </header>

          <ol className="evidence-timeline">
            {profile.evidence.map((evidence) => (
              <li key={evidence.id}>
                <p className="evidence-kind">{evidence.kind}</p>
                <h3>{evidence.label}</h3>
                <p>{evidence.summary}</p>
              </li>
            ))}
          </ol>
        </section>

        <section className="contact-section" id="contact">
          <div>
            <p className="eyebrow">External routes</p>
            <h2>Inspect the work directly</h2>
          </div>

          <div className="contact-links">
            {profile.links.map((link) => (
              <a
                href={link.url}
                key={link.id}
                rel="noreferrer"
                target="_blank"
              >
                <span>{link.label}</span>
                <span aria-hidden="true">↗</span>
              </a>
            ))}
          </div>
        </section>
      </main>

      <footer>
        <p>{profile.displayName} · Engineering Control Room</p>
      </footer>
    </>
  );
}
