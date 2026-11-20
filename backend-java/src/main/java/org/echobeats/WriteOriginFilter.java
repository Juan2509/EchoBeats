package org.echobeats;

import java.io.IOException;
import java.util.Arrays;
import java.util.Set;
import java.util.stream.Collectors;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
class WriteOriginFilter extends OncePerRequestFilter {
    private static final Set<String> SAFE = Set.of("GET","HEAD","OPTIONS");
    private final Set<String> allowed;

    WriteOriginFilter(@Value("${echobeats.allowed-origins}") String origins) {
        allowed = Arrays.stream(origins.split(",")).map(String::strip).collect(Collectors.toUnmodifiableSet());
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
        throws IOException, ServletException {
        String origin = request.getHeader("Origin");
        if (!SAFE.contains(request.getMethod()) && origin != null && !allowed.contains(origin)) {
            response.setStatus(403);
            response.setContentType("application/json");
            response.setCharacterEncoding("UTF-8");
            response.getWriter().write("""
                {"error":{"code":"origin_not_allowed","message":"Origen no permitido."}}
                """);
            return;
        }
        chain.doFilter(request,response);
    }
}
