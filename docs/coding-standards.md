# KEEP — Official Coding Standards & Guidelines (docs/coding-standards.md)

> **Mandatory Code Quality, Typing, Style, and Architecture Rules for All Team Members**  
> *Owner: Member 1 (Project Lead & AI Architect)*

---

## 1. General Principles

1. **Clean Code & SRP**: Every class, module, and function must have a single, well-defined responsibility.
2. **Self-Documenting Code**: Choose descriptive, unambiguous identifiers over cryptic abbreviations.
3. **Strict Typing**: All backend Python code must use explicit type hints; all frontend code must use TypeScript in strict mode.
4. **No Dead Code or Console Logs**: Debug statements (`print()`, `console.log()`) must never be committed to repository branches. Use structured logging instead.
5. **No Hardcoded Secrets**: Passwords, API keys, and credentials must strictly be loaded from environment variables via Pydantic settings or config modules.

---

## 2. Python Backend Standards (Member 1 & Member 2)

- **Language Version**: Python 3.12+
- **Style Guide**: PEP 8 compliance enforced via `ruff` / `black` / `flake8`.
- **Max Function Length**: 40–50 lines maximum. Break long functions into focused private helpers.
- **Type Annotations**:
  ```python
  from typing import List, Optional
  from uuid import UUID

  async def get_document_by_id(
      document_id: UUID, 
      organization_id: UUID
  ) -> Optional[DocumentResponse]:
      """Fetches a document ensuring organization boundary isolation."""
      ...
  ```
- **Docstring Convention**: Google Style docstrings for all public classes and functions.
- **FastAPI Layering**:
  - **Routers (`app/api/v1/`)**: Pure HTTP layer; parses request schemas, calls services, returns response models with proper HTTP status codes.
  - **Services (`app/services/`)**: Business logic, workflow orchestration, transaction management, task publishing.
  - **Repositories (`app/repositories/`)**: Encapsulates database queries and persistence logic.
  - **Models (`app/models/`)**: SQLAlchemy 2.0 ORM database entity declarations.
  - **Schemas (`app/schemas/`)**: Pydantic v2 validation models.

---

## 3. TypeScript & Frontend Standards (Member 3)

- **Language Version**: TypeScript 5+ (Strict Mode enabled).
- **Component Pattern**: Functional React components with explicit props interfaces.
  ```typescript
  interface DocumentCardProps {
    id: string;
    title: string;
    status: "PENDING" | "PROCESSING" | "PROCESSED" | "FAILED";
    onSelect: (id: string) => void;
  }

  export const DocumentCard: React.FC<DocumentCardProps> = ({ id, title, status, onSelect }) => {
    return (
      <div onClick={() => onSelect(id)} className="p-4 border rounded-lg hover:shadow-md transition">
        <h3 className="font-semibold">{title}</h3>
        <span className="text-xs uppercase">{status}</span>
      </div>
    );
  };
  ```
- **Zero `any` Policy**: Use explicit types, generics, or `unknown` with type guards.
- **State Management**: Zustand stores organized cleanly by domain (`useAuthStore`, `useChatStore`, `useDocStore`).
- **Styling**: Tailwind CSS utility classes; avoid inline styles.

---

## 4. Git Commit & Branching Standards

### 4.1 Commit Message Format (Conventional Commits)
```
<type>(<scope>): <short description>
```

**Allowed Types**:
- `feat`: New feature or capability
- `fix`: Bug fix
- `docs`: Documentation updates
- `refactor`: Code changes that neither fix bugs nor add features
- `test`: Adding or correcting tests
- `chore`: Maintenance tasks, dependency updates, configuration

**Examples**:
- `feat(phase-1.1): design system architecture and AI service contracts`
- `fix(auth): correct token expiration calculation in JWT handler`
- `test(rag): add unit tests for reciprocal rank fusion algorithm`

### 4.2 Branch Naming Conventions
- `agent/backend/feature/phase-X.Y-<feature-slug>`
- `agent/frontend/feature/phase-X.Y-<feature-slug>`
- `agent/ingestion/feature/phase-X.Y-<feature-slug>`
- `agent/devops/feature/phase-X.Y-<feature-slug>`
