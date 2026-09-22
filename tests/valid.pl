% Programa completo de prueba
padre(juan, ana).
padre(juan, pedro).

abuelo(X, Z) :-
    padre(X, Y),
    padre(Y, Z).

?- abuelo(juan, Quien).

persona_1('Juan Pérez', "Hola mundo").
X = 10.
Y = 3.1415.
Z = 1.2e-3.
Lista = [a, b | Resto].
Term = {dato}.
A =.. [padre, juan, ana].
B \= C, D == E, F \== G.
N is 10 + 2 * 3 // 2 ** 2 mod 5.
\+ prueba(X).
! ; coma.
p(X) --> q(X).
