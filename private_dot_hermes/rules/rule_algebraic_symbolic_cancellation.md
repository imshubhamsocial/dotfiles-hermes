# Behavioral Invariant: Algebraic_Reasoning Rule
> Inferred from user correction /learn event `evt_7596374ba666`

## Mandate
* INVARIANT: Maintain strict, explicit symbolic cancellation and differential reduction: whenever a variable or expression is algebraically canceled from both sides of an equation, the resulting expression must be written in its final, minimal form, explicitly acknowledging the zero-value state of the canceled term. Do not retain symbols whose coefficient becomes unity, nor retain variables that are proven non-zero through prior constraint checks (e.g., $v \neq 0$).
