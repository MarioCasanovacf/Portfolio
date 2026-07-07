// Barrel export so MDX can do:
//   import { Section, Prose, Figure, CodeBlock, Equation, Quote, Callout } from "~/components/case-study";
//
// `Code.astro` is exported under the canonical name `CodeBlock` to match the
// MDX delivery contract. Both names resolve to the same component.

export { default as Section } from './Section.astro';
export { default as Prose } from './Prose.astro';
export { default as Figure } from './Figure.astro';
export { default as CodeBlock } from './Code.astro';
export { default as Equation } from './Equation.astro';
export { default as Quote } from './Quote.astro';
export { default as Callout } from './Callout.astro';
